from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ..models import Address, AfterSale, CartItem, Order, OrderItem, Review, Sku
from ..responses import fail, ok
from ..serializers import (
    AddressSerializer,
    AfterSaleSerializer,
    OrderSerializer,
)
from ..utils import gen_no, paginate


# ---------------------------------------------------------------- 收货地址
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def addresses(request):
    if request.method == "GET":
        return ok(AddressSerializer(Address.objects.filter(user=request.user), many=True).data)
    serializer = AddressSerializer(data=request.data)
    if not serializer.is_valid():
        return fail(next(iter(serializer.errors.values()))[0], 40001)
    with transaction.atomic():
        if (
            serializer.validated_data.get("is_default")
            or not Address.objects.filter(user=request.user).exists()
        ):
            Address.objects.filter(user=request.user).update(is_default=False)
            address = serializer.save(user=request.user, is_default=True)
        else:
            address = serializer.save(user=request.user)
    return ok(AddressSerializer(address).data, "地址已保存", 201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def address_detail(request, pk):
    address = Address.objects.filter(pk=pk, user=request.user).first()
    if not address:
        return fail("地址不存在", 40404, 404)
    if request.method == "DELETE":
        address.delete()
        return ok(None, "地址已删除")
    with transaction.atomic():
        if request.data.get("is_default"):
            Address.objects.filter(user=request.user).update(is_default=False)
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if not serializer.is_valid():
            return fail(next(iter(serializer.errors.values()))[0], 40001)
        serializer.save()
    return ok(serializer.data, "地址已更新")


# ---------------------------------------------------------------- 订单
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def orders(request):
    if request.method == "GET":
        qs = Order.objects.filter(user=request.user).prefetch_related("items__shop")
        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(items__title_snapshot__icontains=q).distinct()
        return ok(paginate(qs, request, OrderSerializer))

    address = None
    if request.data.get("address_id"):
        address = Address.objects.filter(pk=request.data["address_id"], user=request.user).first()
        if not address:
            return fail("请选择有效的收货地址")
    if not address:
        address = (
            Address.objects.filter(user=request.user, is_default=True).first()
            or Address.objects.filter(user=request.user).first()
        )
    if not address:
        return fail("请先添加收货地址")

    # 立即购买：不经过购物车，直接对单个 SKU 下单
    if request.data.get("sku_id"):
        try:
            qty = max(1, int(request.data.get("quantity", 1)))
        except (TypeError, ValueError):
            qty = 1
        with transaction.atomic():
            sku = (
                Sku.objects.select_for_update()
                .select_related("spu__shop")
                .filter(pk=request.data["sku_id"], enabled=True)
                .first()
            )
            if not sku or sku.spu.status != "on":
                return fail("商品已下架")
            if sku.stock < qty:
                return fail(f"库存不足，仅剩 {sku.stock} 件")
            subtotal = sku.price * qty
            freight = Decimal("0") if subtotal >= 99 else Decimal("8")
            order = Order.objects.create(
                order_no=gen_no("O"),
                batch_no=gen_no("B"),
                user=request.user,
                address=address,
                address_snapshot={
                    "receiver": address.receiver,
                    "phone": address.phone,
                    "full_text": address.full_text,
                },
                subtotal=subtotal,
                freight=freight,
                total=subtotal + freight,
                remark=str(request.data.get("remark", ""))[:255],
            )
            Sku.objects.filter(pk=sku.id).update(stock=F("stock") - qty)
            OrderItem.objects.create(
                order=order,
                sku=sku,
                shop=sku.spu.shop,
                title_snapshot=sku.spu.title,
                specs_snapshot=sku.specs,
                price_snapshot=sku.price,
                quantity=qty,
                image_seed=sku.spu.image_seed,
            )
        return ok(
            {
                "batch_no": order.batch_no,
                "total": str(order.total),
                "orders": OrderSerializer([order], many=True).data,
            },
            "订单提交成功",
            201,
        )

    with transaction.atomic():
        cart_items = list(
            CartItem.objects.select_for_update()
            .filter(user=request.user, selected=True)
            .select_related("sku__spu__shop")
            .order_by("id")
        )
        if not cart_items:
            return fail("请先选择要结算的商品")
        sku_ids = sorted({item.sku_id for item in cart_items})
        locked = {sku.id: sku for sku in Sku.objects.select_for_update().filter(id__in=sku_ids)}
        for item in cart_items:
            sku = locked.get(item.sku_id)
            if not sku or sku.spu.status != "on" or not sku.enabled:
                return fail(f"《{item.sku.spu.title}》已下架，请移除后重试")
            if sku.stock < item.quantity:
                return fail(f"《{sku.spu.title}》库存不足，仅剩 {sku.stock} 件")

        snapshot = {
            "receiver": address.receiver,
            "phone": address.phone,
            "full_text": address.full_text,
        }
        batch_no = gen_no("B")
        groups = defaultdict(list)
        for item in cart_items:
            groups[item.sku.spu.shop_id].append(item)

        created_orders = []
        for shop_items in groups.values():
            subtotal = sum((item.sku.price * item.quantity for item in shop_items), Decimal("0"))
            freight = Decimal("0") if subtotal >= 99 else Decimal("8")
            order = Order.objects.create(
                order_no=gen_no("O"),
                batch_no=batch_no,
                user=request.user,
                address=address,
                address_snapshot=snapshot,
                subtotal=subtotal,
                freight=freight,
                total=subtotal + freight,
                remark=str(request.data.get("remark", ""))[:255],
            )
            for item in shop_items:
                sku = locked[item.sku_id]
                Sku.objects.filter(pk=sku.id).update(stock=F("stock") - item.quantity)
                OrderItem.objects.create(
                    order=order,
                    sku=sku,
                    shop=sku.spu.shop,
                    title_snapshot=sku.spu.title,
                    specs_snapshot=sku.specs,
                    price_snapshot=sku.price,
                    quantity=item.quantity,
                    image_seed=sku.spu.image_seed,
                )
                item.delete()
            created_orders.append(order)

    data = {
        "batch_no": batch_no,
        "total": str(sum((o.total for o in created_orders), Decimal("0"))),
        "orders": OrderSerializer(created_orders, many=True).data,
    }
    return ok(data, "订单提交成功", 201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail(request, order_no):
    order = (
        Order.objects.filter(order_no=order_no, user=request.user)
        .prefetch_related("items__shop", "items__aftersales")
        .first()
    )
    if not order:
        return fail("订单不存在", 40404, 404)
    data = OrderSerializer(order).data
    data["aftersales"] = AfterSaleSerializer(
        AfterSale.objects.filter(order_item__order=order).select_related("order_item__shop"),
        many=True,
    ).data
    return ok(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def batch_orders(request, batch_no):
    qs = Order.objects.filter(batch_no=batch_no, user=request.user).prefetch_related("items__shop")
    if not qs.exists():
        return fail("订单不存在", 40404, 404)
    orders = list(qs)
    return ok(
        {
            "batch_no": batch_no,
            "orders": OrderSerializer(orders, many=True).data,
            "total": str(sum((o.total for o in orders), Decimal("0"))),
            "payable": any(o.status == "pending_pay" for o in orders),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def order_action(request, order_no, action):
    order = (
        Order.objects.filter(order_no=order_no, user=request.user)
        .prefetch_related("items__sku")
        .first()
    )
    if not order:
        return fail("订单不存在", 40404, 404)
    rules = {"cancel": ("pending_pay", "cancelled"), "confirm": ("shipped", "completed")}
    if action not in rules or order.status != rules[action][0]:
        return fail("当前订单状态不支持该操作")
    with transaction.atomic():
        if action == "cancel":
            for item in order.items.all():
                if item.sku_id:
                    Sku.objects.filter(pk=item.sku_id).update(stock=F("stock") + item.quantity)
            order.status = "cancelled"
            order.cancel_reason = request.data.get("reason", "用户主动取消")
        else:
            order.status = "completed"
            order.completed_at = timezone.now()
            order.items.update(reviewed=False)
        order.save(update_fields=["status", "cancel_reason", "completed_at"])
    return ok(OrderSerializer(order).data, "操作成功")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_mock(request):
    """模拟支付：支持单个订单号或整批订单号。"""
    order_no = request.data.get("order_no")
    batch_no = request.data.get("batch_no")
    qs = Order.objects.filter(user=request.user, status="pending_pay")
    if order_no:
        qs = qs.filter(order_no=order_no)
    elif batch_no:
        qs = qs.filter(batch_no=batch_no)
    else:
        return fail("缺少订单号")
    if not qs.exists():
        return fail("没有待支付的订单", 40404, 404)
    # 先取数量与批次号，update 之后 status 已变化，再做聚合会得到 0
    paid_count = qs.count()
    first = qs.first()
    paid_batch = batch_no or first.batch_no
    now = timezone.now()
    qs.update(status="paid", paid_at=now, pay_method=request.data.get("method", "mock"))
    return ok({"batch_no": paid_batch, "paid": paid_count}, "支付成功")


# ---------------------------------------------------------------- 评价与售后
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reviews(request):
    order = (
        Order.objects.filter(
            order_no=request.data.get("order_no"), user=request.user, status="completed"
        )
        .prefetch_related("items__sku")
        .first()
    )
    if not order:
        return fail("订单不可评价")
    payload = request.data.get("items") or []
    mapping = {row.get("order_item_id"): row for row in payload if isinstance(row, dict)}
    count = 0
    for item in order.items.all():
        if item.reviewed or not item.sku_id:
            continue
        row = mapping.get(item.id, {})
        Review.objects.create(
            spu=item.sku.spu,
            user=request.user,
            order_no=order.order_no,
            rating=int(row.get("rating", request.data.get("rating", 5))),
            content=row.get("content")
            or request.data.get("content")
            or "商品不错，物流很快，值得推荐。",
        )
        item.reviewed = True
        item.save(update_fields=["reviewed"])
        spu = item.sku.spu
        spu.review_count = spu.reviews.count()
        spu.save(update_fields=["review_count"])
        count += 1
    if not count:
        return fail("该订单已评价")
    return ok({"count": count}, "评价成功")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_reviews(request):
    qs = Review.objects.filter(user=request.user).select_related("spu")
    return ok(
        [
            {
                "id": r.id,
                "spu_id": r.spu_id,
                "title": r.spu.title,
                "image_seed": r.spu.image_seed,
                "rating": r.rating,
                "content": r.content,
                "reply": r.reply,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for r in qs
        ]
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def aftersales(request):
    if request.method == "GET":
        qs = AfterSale.objects.filter(user=request.user).select_related(
            "order_item__order", "order_item__shop"
        )
        return ok(AfterSaleSerializer(qs, many=True).data)
    item = (
        OrderItem.objects.filter(pk=request.data.get("order_item_id"), order__user=request.user)
        .select_related("order")
        .first()
    )
    if not item:
        return fail("订单商品不存在", 40404, 404)
    if item.order.status not in ("paid", "shipped", "completed"):
        return fail("当前订单状态不支持申请售后")
    if item.aftersales.exclude(status="rejected").exists():
        return fail("该商品已有售后记录")
    sale = AfterSale.objects.create(
        order_item=item,
        user=request.user,
        type=request.data.get("type", "refund"),
        reason=request.data.get("reason", "商品与描述不符")[:255],
        description=request.data.get("description", "")[:255],
        amount=item.price_snapshot * item.quantity,
    )
    item.order.status = "aftersale"
    item.order.save(update_fields=["status"])
    return ok(AfterSaleSerializer(sale).data, "售后申请已提交", 201)
