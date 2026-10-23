"""平台后台：数据看板、类目、商家、商品审核、订单、售后。"""

from datetime import timedelta

from django.db.models import Count, F, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes

from ..models import (
    AfterSale,
    Category,
    Order,
    Shop,
    Sku,
    Spu,
    User,
)
from ..permissions import IsConsole
from ..responses import fail, ok
from ..serializers import (
    AfterSaleSerializer,
    CategorySerializer,
    OrderSerializer,
    ProductListSerializer,
    ShopSerializer,
)
from ..utils import paginate


@api_view(["GET"])
@permission_classes([IsConsole])
def dashboard(request):
    today = timezone.localdate()
    orders = Order.objects.all()
    valid = orders.exclude(status__in=["cancelled", "pending_pay"])
    start = today - timedelta(days=6)
    trend = []
    for offset in range(7):
        day = start + timedelta(days=offset)
        trend.append(
            {
                "date": day.strftime("%m-%d"),
                "orders": orders.filter(created_at__date=day).count(),
                "gmv": float(
                    valid.filter(created_at__date=day).aggregate(v=Sum("total"))["v"] or 0
                ),
            }
        )
    ranking = Shop.objects.annotate(
        order_count=Count("orderitem__order", distinct=True),
        gmv=Sum(F("orderitem__price_snapshot") * F("orderitem__quantity")),
    ).order_by("-gmv")[:8]
    categories = (
        Category.objects.filter(level=1)
        .annotate(value=Count("children__children__spus", distinct=True))
        .values("name", "value")
        .order_by("-value")[:8]
    )
    return ok(
        {
            "stats": {
                "gmv": str(valid.aggregate(v=Sum("total"))["v"] or 0),
                "today_gmv": str(
                    valid.filter(created_at__date=today).aggregate(v=Sum("total"))["v"] or 0
                ),
                "orders": orders.count(),
                "today_orders": orders.filter(created_at__date=today).count(),
                "buyers": User.objects.filter(role="buyer").count(),
                "shops": Shop.objects.count(),
                "pending_products": Spu.objects.filter(status="pending").count(),
                "pending_shops": Shop.objects.filter(approved=False).count(),
                "pending_aftersales": AfterSale.objects.filter(status="pending").count(),
                "products": Spu.objects.count(),
            },
            "trend": trend,
            "shop_ranking": [
                {"name": s.name, "orders": s.order_count, "gmv": float(s.gmv or 0)} for s in ranking
            ],
            "categories": list(categories),
            "recent_orders": OrderSerializer(
                orders.prefetch_related("items__shop")[:8], many=True
            ).data,
        }
    )


# ---------------------------------------------------------------- 类目


@api_view(["GET", "POST"])
@permission_classes([IsConsole])
def categories(request):
    if request.method == "GET":
        roots = Category.objects.filter(parent__isnull=True).prefetch_related("children__children")
        return ok(CategorySerializer(roots, many=True, context={"include_disabled": True}).data)
    name = str(request.data.get("name", "")).strip()
    parent = (
        Category.objects.filter(pk=request.data.get("parent")).first()
        if request.data.get("parent")
        else None
    )
    level = (parent.level + 1) if parent else 1
    if not name:
        return fail("请填写类目名称")
    if level > 3:
        return fail("最多支持三级类目")
    category = Category.objects.create(
        name=name,
        parent=parent,
        level=level,
        sort=int(request.data.get("sort", Category.objects.filter(parent=parent).count())),
        icon=request.data.get("icon", "▦"),
        enabled=True,
    )
    return ok(
        CategorySerializer(category, context={"include_disabled": True}).data, "类目已新增", 201
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsConsole])
def category_detail(request, pk):
    category = Category.objects.filter(pk=pk).prefetch_related("children").first()
    if not category:
        return fail("类目不存在", 40404, 404)
    if request.method == "DELETE":
        if category.children.exists():
            return fail("请先删除子类目")
        if category.spus.exists():
            return fail("该类目下仍有商品，无法删除")
        category.delete()
        return ok(None, "类目已删除")
    if "name" in request.data:
        category.name = request.data["name"]
    if "enabled" in request.data:
        category.enabled = bool(request.data["enabled"])
    if "sort" in request.data:
        category.sort = int(request.data["sort"])
    category.save()
    return ok(CategorySerializer(category).data, "类目已更新")


# ---------------------------------------------------------------- 商家


@api_view(["GET"])
@permission_classes([IsConsole])
def shops(request):
    qs = Shop.objects.select_related("owner").annotate(product_count=Count("spus", distinct=True))
    if request.query_params.get("approved") in ("true", "false"):
        qs = qs.filter(approved=request.query_params["approved"] == "true")
    if request.query_params.get("q"):
        qs = qs.filter(name__icontains=request.query_params["q"])
    return ok([{**ShopSerializer(shop).data, "product_count": shop.product_count} for shop in qs])


@api_view(["POST"])
@permission_classes([IsConsole])
def shop_audit(request, pk):
    shop = Shop.objects.filter(pk=pk).first()
    if not shop:
        return fail("店铺不存在", 40404, 404)
    action = request.data.get("action")
    if action == "approve":
        shop.approved = True
        shop.enabled = True
    elif action == "reject":
        shop.approved = False
    elif action == "disable":
        shop.enabled = False
    elif action == "enable":
        shop.enabled = True
    else:
        return fail("操作类型不正确")
    shop.save()
    return ok(ShopSerializer(shop).data, "操作成功")


# ---------------------------------------------------------------- 商品审核


@api_view(["GET"])
@permission_classes([IsConsole])
def products(request):
    qs = Spu.objects.select_related("brand", "shop", "category").prefetch_related("skus")
    params = request.query_params
    if params.get("status"):
        qs = qs.filter(status=params["status"])
    if params.get("q"):
        qs = qs.filter(title__icontains=params["q"])
    if params.get("shop"):
        qs = qs.filter(shop_id=params["shop"])
    return ok(paginate(qs, request, ProductListSerializer, default_size=10))


@api_view(["POST"])
@permission_classes([IsConsole])
def product_audit(request, pk):
    spu = Spu.objects.filter(pk=pk).first()
    if not spu:
        return fail("商品不存在", 40404, 404)
    action = request.data.get("action")
    if action == "approve":
        spu.status = "on"
        spu.reject_reason = ""
    elif action == "reject":
        spu.status = "rejected"
        spu.reject_reason = str(request.data.get("reason", "商品信息不完整"))[:200]
    elif action == "off":
        spu.status = "off"
    elif action == "on":
        spu.status = "on"
    else:
        return fail("操作类型不正确")
    spu.save()
    return ok(ProductListSerializer(spu).data, "审核完成")


# ---------------------------------------------------------------- 订单 / 售后


@api_view(["GET"])
@permission_classes([IsConsole])
def orders(request):
    qs = Order.objects.all().prefetch_related("items__shop")
    params = request.query_params
    if params.get("status"):
        qs = qs.filter(status=params["status"])
    if params.get("q"):
        qs = qs.filter(order_no__icontains=params["q"]) | qs.filter(
            items__title_snapshot__icontains=params["q"]
        )
    if params.get("shop"):
        qs = qs.filter(items__shop_id=params["shop"]).distinct()
    return ok(paginate(qs.distinct(), request, OrderSerializer, default_size=10))


@api_view(["GET", "POST"])
@permission_classes([IsConsole])
def aftersales(request):
    if request.method == "GET":
        qs = AfterSale.objects.select_related("order_item__order", "order_item__shop")
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        return ok(AfterSaleSerializer(qs, many=True).data)
    sale = AfterSale.objects.filter(pk=request.data.get("id")).select_related("order_item").first()
    if not sale:
        return fail("售后单不存在", 40404, 404)
    if sale.status != "pending":
        return fail("该售后单已处理")
    action = request.data.get("action")
    if action not in ("approve", "reject"):
        return fail("操作类型不正确")
    sale.reply = str(request.data.get("reply", "平台已介入处理"))[:255]
    sale.handled_at = timezone.now()
    item = sale.order_item
    if action == "approve":
        sale.status = "refunded"
        # 退款成功需要把库存还回商品，避免平台侧处理后库存少卖
        if item.sku_id:
            Sku.objects.filter(pk=item.sku_id).update(stock=F("stock") + item.quantity)
        Order.objects.filter(pk=item.order_id).update(status="refunded")
    else:
        sale.status = "rejected"
        Order.objects.filter(pk=item.order_id).update(status="completed")
    sale.save()
    return ok(AfterSaleSerializer(sale).data, "处理完成")


# ---------------------------------------------------------------- 内容运营
