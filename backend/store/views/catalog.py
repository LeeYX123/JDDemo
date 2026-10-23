from django.db.models import Max, Min, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from ..models import (
    Banner,
    Brand,
    Category,
    Coupon,
    HomeFloor,
    Notice,
    Review,
    SeckillActivity,
    Spu,
)
from ..responses import fail, ok
from ..serializers import (
    BannerSerializer,
    BrandSerializer,
    CategorySerializer,
    CouponSerializer,
    HomeFloorSerializer,
    NoticeSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ReviewSerializer,
    SeckillActivitySerializer,
)
from ..utils import category_scope, paginate

ORDERING_MAP = {
    "default": "-sales",
    "sales": "-sales",
    "new": "-created_at",
    "price_asc": "min_price",
    "price_desc": "-min_price",
    "rating": "-rating",
}


def base_products():
    return (
        Spu.objects.filter(status="on")
        .select_related("brand", "shop", "category")
        .prefetch_related("skus")
        .annotate(min_price=Min("skus__price"), max_price=Max("skus__price"))
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def categories(request):
    roots = Category.objects.filter(parent__isnull=True, enabled=True).prefetch_related(
        "children__children"
    )
    return ok(CategorySerializer(roots, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def brands(request):
    qs = Brand.objects.filter(enabled=True)
    if request.query_params.get("category"):
        qs = qs.filter(spus__category_id=request.query_params["category"]).distinct()
    return ok(BrandSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def banners(request):
    return ok(BannerSerializer(Banner.objects.filter(enabled=True), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def notices(request):
    return ok(NoticeSerializer(Notice.objects.filter(enabled=True), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def floors(request):
    return ok(HomeFloorSerializer(HomeFloor.objects.filter(enabled=True), many=True).data)


def _floor_products(floor, tab=0, size=6):
    qs = base_products()
    if floor.category_id:
        qs = qs.filter(category_id__in=category_scope(floor.category))
    order = {0: "-sales", 1: "-created_at", 2: "min_price"}.get(int(tab), "-sales")
    return ProductListSerializer(qs.order_by(order)[:size], many=True).data


@api_view(["GET"])
@permission_classes([AllowAny])
def home(request):
    roots = Category.objects.filter(parent__isnull=True, enabled=True).prefetch_related(
        "children__children"
    )
    floor_list = list(HomeFloor.objects.filter(enabled=True).select_related("category"))
    floor_data = []
    for floor in floor_list:
        item = HomeFloorSerializer(floor).data
        item["products"] = _floor_products(floor, 0, 6)
        floor_data.append(item)

    now = timezone.now()
    activity = (
        SeckillActivity.objects.filter(enabled=True, end_at__gte=now)
        .prefetch_related("items__sku__spu")
        .order_by("start_at")
        .first()
    )
    guess = base_products().order_by("-sales", "-review_count")[:12]
    return ok(
        {
            "categories": CategorySerializer(roots, many=True).data,
            "banners": BannerSerializer(Banner.objects.filter(enabled=True), many=True).data,
            "notices": NoticeSerializer(Notice.objects.filter(enabled=True), many=True).data,
            "floors": floor_data,
            "seckill": SeckillActivitySerializer(activity).data if activity else None,
            "guess": ProductListSerializer(guess, many=True).data,
            "coupons": CouponSerializer(
                Coupon.objects.filter(enabled=True)[:4], many=True, context={"request": request}
            ).data,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def products(request):
    qs = base_products()
    params = request.query_params
    q = params.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(subtitle__icontains=q)
            | Q(tags__icontains=q)
            | Q(brand__name__icontains=q)
            | Q(category__name__icontains=q)
            | Q(category__parent__name__icontains=q)
            | Q(category__parent__parent__name__icontains=q)
        )
    if params.get("category"):
        category = (
            Category.objects.filter(pk=params["category"])
            .prefetch_related("children__children")
            .first()
        )
        if category:
            qs = qs.filter(category_id__in=category_scope(category))
    if params.get("brand"):
        qs = qs.filter(brand_id__in=[v for v in params["brand"].split(",") if v.isdigit()])
    if params.get("shop"):
        qs = qs.filter(shop_id=params["shop"])
    try:
        if params.get("min_price"):
            qs = qs.filter(min_price__gte=params["min_price"])
        if params.get("max_price"):
            qs = qs.filter(min_price__lte=params["max_price"])
    except (ValueError, TypeError):
        return fail("价格区间格式不正确")
    if params.get("floor"):
        floor = HomeFloor.objects.filter(pk=params["floor"]).select_related("category").first()
        if floor and floor.category_id:
            qs = qs.filter(category_id__in=category_scope(floor.category))
    if params.get("in_stock") == "1":
        qs = qs.filter(skus__stock__gt=0).distinct()

    ordering = ORDERING_MAP.get(params.get("ordering", "default"), "-sales")
    if params.get("floor") and params.get("tab"):
        ordering = {0: "-sales", 1: "-created_at", 2: "min_price"}.get(
            int(params.get("tab", 0) or 0), ordering
        )
    qs = qs.order_by(ordering, "-id")
    return ok(paginate(qs, request, ProductListSerializer, {"request": request}))


@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail(request, pk):
    product = (
        Spu.objects.select_related("brand", "shop", "category")
        .prefetch_related("skus", "reviews__user", "category__parent__parent")
        .filter(pk=pk)
        .first()
    )
    if not product or product.status not in ("on", "off"):
        return fail("商品不存在或已下架", 40404, 404)
    data = ProductDetailSerializer(product, context={"request": request}).data
    data["related"] = ProductListSerializer(
        base_products().filter(category_id=product.category_id).exclude(pk=pk)[:6], many=True
    ).data
    return ok(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def product_reviews(request, pk):
    qs = Review.objects.filter(spu_id=pk).select_related("user")
    if request.query_params.get("rating"):
        qs = qs.filter(rating=request.query_params["rating"])
    return ok(paginate(qs, request, ReviewSerializer, default_size=10))


@api_view(["GET"])
@permission_classes([AllowAny])
def seckill(request):
    now = timezone.now()
    activities = (
        SeckillActivity.objects.filter(enabled=True, end_at__gte=now)
        .prefetch_related("items__sku__spu")
        .order_by("start_at")
    )
    return ok(SeckillActivitySerializer(activities, many=True).data)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def coupons(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return fail("请先登录", 40101, 401)
        coupon = Coupon.objects.filter(pk=request.data.get("coupon_id"), enabled=True).first()
        if not coupon:
            return fail("优惠券不存在", 40404, 404)
        if coupon.users.filter(id=request.user.id).exists():
            return fail("您已领取过该优惠券")
        if coupon.claimed >= coupon.total:
            return fail("优惠券已抢光")
        coupon.users.add(request.user)
        coupon.claimed += 1
        coupon.save(update_fields=["claimed"])
        return ok(None, "领取成功")
    qs = Coupon.objects.filter(enabled=True)
    if request.query_params.get("mine") == "1" and request.user.is_authenticated:
        qs = qs.filter(users=request.user)
    return ok(CouponSerializer(qs, many=True, context={"request": request}).data)
