from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes

from ..models import AfterSale, Brand, Category, Order, OrderItem, Shop, Sku, Spu
from ..permissions import IsMerchant
from ..responses import fail, ok
from ..serializers import (
    AfterSaleSerializer,
    OrderSerializer,
    ProductListSerializer,
    ShopSerializer,
)
from ..utils import paginate


def current_shop(user):
    shop = Shop.objects.filter(owner=user).first()
    if shop:
        return shop
    if user.role == "console":
        return Shop.objects.first()
    return None


@api_view(["GET"])
@permission_classes([IsMerchant])
def dashboard(request):
    shop = current_shop(request.user)
    if not shop:
        return fail("当前账号未绑定店铺", 40302, 403)
    today = timezone.localdate()
    items = OrderItem.objects.filter(shop=shop)
    paid_items = items.filter(order__status__in=["paid", "shipped", "completed"])
    start = today - timedelta(days=6)
    trend = []
    for offset in range(7):
        day = start + timedelta(days=offset)
        trend.append(
            {
                "date": day.strftime("%m-%d"),
                "orders": Order.objects.filter(items__shop=shop, created_at__date=day)
                .distinct()
                .count(),
                "gmv": float(
                    items.filter(order__created_at__date=day).aggregate(
                        v=Sum(F("price_snapshot") * F("quantity"))
                    )["v"]
                    or 0
                ),
            }
        )
    top = (
        items.filter(order__status__in=["paid", "shipped", "completed"])
        .values("title_snapshot")
        .annotate(sales=Sum("quantity"), amount=Sum(F("price_snapshot") * F("quantity")))
        .order_by("-sales")[:5]
    )
    recent = Order.objects.filter(items__shop=shop).distinct().prefetch_related("items__shop")[:8]
    return ok(
        {
            "shop": ShopSerializer(shop).data,
            "stats": {
                "today_orders": Order.objects.filter(items__shop=shop, created_at__date=today)
                .distinct()
                .count(),
                "today_gmv": str(
                    items.filter(order__created_at__date=today).aggregate(
                        v=Sum(F("price_snapshot") * F("quantity"))
                    )["v"]
                    or 0
                ),
                "gmv": str(
                    paid_items.aggregate(v=Sum(F("price_snapshot") * F("quantity")))["v"] or 0
                ),
                "pending_ship": items.filter(order__status="paid")
                .values("order")
                .distinct()
                .count(),
                "pending_aftersale": AfterSale.objects.filter(
                    order_item__shop=shop, status="pending"
                ).count(),
                "on_sale": Spu.objects.filter(shop=shop, status="on").count(),
                "products": Spu.objects.filter(shop=shop).count(),
                "orders": Order.objects.filter(items__shop=shop).distinct().count(),
            },
            "trend": trend,
            "top_products": list(top),
            "recent_orders": OrderSerializer(recent, many=True).data,
        }
    )


# ---------------------------------------------------------------- 商品
@api_view(["GET", "POST"])
@permission_classes([IsMerchant])
def products(request):
    shop = current_shop(request.user)
    if not shop:
        return fail("当前账号未绑定店铺", 40302, 403)
    if request.method == "GET":
        qs = (
            Spu.objects.filter(shop=shop)
            .select_related("brand", "shop", "category")
            .prefetch_related("skus")
        )
        if request.query_params.get("q"):
            qs = qs.filter(title__icontains=request.query_params["q"])
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        return ok(paginate(qs, request, ProductListSerializer, default_size=10))

    title = str(request.data.get("title", "")).strip()
    category = Category.objects.filter(pk=request.data.get("category_id"), level=3).first()
    brand = Brand.objects.filter(pk=request.data.get("brand_id")).first()
    if not title or not category or not brand:
        return fail("请填写商品标题，并选择三级类目与品牌")
    try:
        price = Decimal(str(request.data.get("price", 0)))
        market_price = Decimal(str(request.data.get("market_price", price)))
        stock = int(request.data.get("stock", 100))
    except Exception:
        return fail("价格或库存格式不正确")
    if price <= 0:
        return fail("售价必须大于 0")
    spu = Spu.objects.create(
        title=title,
        subtitle=str(request.data.get("subtitle", ""))[:255],
        category=category,
        brand=brand,
        shop=shop,
        image_seed=int(request.data.get("image_seed", 1)),
        tags=request.data.get("tags", "新品|自营"),
        status=request.data.get("status", "pending"),
        detail=request.data.get("detail", "严选材质，正品保障。"),
        sales=0,
        review_count=0,
    )
    Sku.objects.create(
        spu=spu,
        name=request.data.get("spec", "标准版"),
        specs={"规格": request.data.get("spec", "标准版")},
        price=price,
        market_price=market_price if market_price >= price else price,
        stock=stock,
        image_seed=spu.image_seed,
    )
    return ok(ProductListSerializer(spu).data, "商品已提交，等待平台审核", 201)


@api_view(["PATCH"])
@permission_classes([IsMerchant])
def product_detail(request, pk):
    shop = current_shop(request.user)
    spu = Spu.objects.filter(pk=pk, shop=shop).prefetch_related("skus").first()
    if not spu:
        return fail("商品不存在", 40404, 404)
    for field in ("title", "subtitle", "tags", "detail"):
        if field in request.data:
            setattr(spu, field, request.data[field])
    if request.data.get("category_id"):
        category = Category.objects.filter(pk=request.data["category_id"], level=3).first()
        if category:
            spu.category = category
    if request.data.get("brand_id"):
        brand = Brand.objects.filter(pk=request.data["brand_id"]).first()
        if brand:
            spu.brand = brand
    if request.data.get("status") in ("on", "off", "draft", "pending"):
        spu.status = request.data["status"]
    spu.save()
    sku = spu.skus.first()
    if sku:
        for field, attr in (
            ("price", "price"),
            ("market_price", "market_price"),
            ("stock", "stock"),
        ):
            if field in request.data:
                setattr(
                    sku,
                    attr,
                    (
                        Decimal(str(request.data[field]))
                        if field != "stock"
                        else int(request.data[field])
                    ),
                )
        sku.save()
    return ok(ProductListSerializer(spu).data, "已保存")


@api_view(["POST"])
@permission_classes([IsMerchant])
def product_toggle(request, pk):
    shop = current_shop(request.user)
    spu = Spu.objects.filter(pk=pk, shop=shop).first()
    if not spu:
        return fail("商品不存在", 40404, 404)
    spu.status = "off" if spu.status == "on" else "on"
    spu.save(update_fields=["status"])
    return ok({"id": spu.id, "status": spu.status}, "已下架" if spu.status == "off" else "已上架")


# ---------------------------------------------------------------- 订单
@api_view(["GET"])
@permission_classes([IsMerchant])
def orders(request):
    shop = current_shop(request.user)
    if not shop:
        return fail("当前账号未绑定店铺", 40302, 403)
    qs = Order.objects.filter(items__shop=shop).distinct().prefetch_related("items__shop")
    if request.query_params.get("status"):
        qs = qs.filter(status=request.query_params["status"])
    if request.query_params.get("q"):
        key = request.query_params["q"]
        qs = qs.filter(order_no__icontains=key) | qs.filter(items__title_snapshot__icontains=key)
    return ok(paginate(qs, request, OrderSerializer, default_size=10))


@api_view(["POST"])
@permission_classes([IsMerchant])
def ship(request, order_no):
    shop = current_shop(request.user)
    order = Order.objects.filter(order_no=order_no, items__shop=shop).distinct().first()
    if not order:
        return fail("订单不存在", 40404, 404)
    if order.status != "paid":
        return fail("只有待发货订单可以发货")
    tracking_no = str(request.data.get("tracking_no", "")).strip()
    if len(tracking_no) < 6:
        return fail("请填写有效的运单号（至少 6 位）")
    order.status = "shipped"
    order.tracking_no = tracking_no
    order.tracking_company = request.data.get("tracking_company", "京东物流")
    order.shipped_at = timezone.now()
    order.save(update_fields=["status", "tracking_no", "tracking_company", "shipped_at"])
    return ok(OrderSerializer(order).data, "发货成功")


# ---------------------------------------------------------------- 售后
@api_view(["GET", "POST"])
@permission_classes([IsMerchant])
def aftersales(request):
    shop = current_shop(request.user)
    if request.method == "GET":
        qs = AfterSale.objects.filter(order_item__shop=shop).select_related(
            "order_item__order", "order_item__shop"
        )
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        return ok(AfterSaleSerializer(qs, many=True).data)
    sale = (
        AfterSale.objects.filter(pk=request.data.get("id"), order_item__shop=shop)
        .select_related("order_item")
        .first()
    )
    if not sale:
        return fail("售后单不存在", 40404, 404)
    if sale.status != "pending":
        return fail("该售后单已处理")
    action = request.data.get("action")
    if action not in ("approve", "reject"):
        return fail("操作类型不正确")
    sale.reply = str(request.data.get("reply", ""))[:255]
    sale.handled_at = timezone.now()
    if action == "approve":
        sale.status = "refunded"
        item = sale.order_item
        if item.sku_id:
            Sku.objects.filter(pk=item.sku_id).update(stock=F("stock") + item.quantity)
        Order.objects.filter(pk=item.order_id).update(status="refunded")
    else:
        sale.status = "rejected"
        Order.objects.filter(pk=sale.order_item.order_id).update(status="completed")
    sale.save()
    return ok(AfterSaleSerializer(sale).data, "已同意售后" if action == "approve" else "已驳回售后")


@api_view(["GET", "PATCH"])
@permission_classes([IsMerchant])
def shop_profile(request):
    shop = current_shop(request.user)
    if not shop:
        return fail("当前账号未绑定店铺", 40302, 403)
    if request.method == "PATCH":
        for field in ("name", "description", "logo"):
            if field in request.data:
                setattr(shop, field, request.data[field])
        shop.save()
    product_count = Spu.objects.filter(shop=shop).count()
    data = ShopSerializer(shop).data
    data["product_count"] = product_count
    data["order_count"] = Order.objects.filter(items__shop=shop).distinct().count()
    return ok(data)
