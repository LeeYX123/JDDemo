"""平台后台：内容运营（轮播/楼层/快报）、用户与优惠券。"""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes

from ..models import (
    Banner,
    Coupon,
    HomeFloor,
    Notice,
    User,
)
from ..permissions import IsConsole
from ..responses import fail, ok
from ..serializers import (
    BannerSerializer,
    HomeFloorSerializer,
    NoticeSerializer,
    UserSerializer,
)
from ..utils import paginate


@api_view(["GET", "POST"])
@permission_classes([IsConsole])
def banners(request):
    if request.method == "GET":
        return ok(BannerSerializer(Banner.objects.all(), many=True).data)
    serializer = BannerSerializer(data=request.data)
    if not serializer.is_valid():
        return fail(next(iter(serializer.errors.values()))[0])
    serializer.save()
    return ok(serializer.data, "轮播已创建", 201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsConsole])
def banner_detail(request, pk):
    banner = Banner.objects.filter(pk=pk).first()
    if not banner:
        return fail("轮播不存在", 40404, 404)
    if request.method == "DELETE":
        banner.delete()
        return ok(None, "轮播已删除")
    for field in ("title", "subtitle", "color", "image_seed", "link", "enabled", "sort"):
        if field in request.data:
            setattr(banner, field, request.data[field])
    banner.save()
    return ok(BannerSerializer(banner).data, "轮播已更新")


@api_view(["GET", "POST"])
@permission_classes([IsConsole])
def floors(request):
    if request.method == "GET":
        return ok(HomeFloorSerializer(HomeFloor.objects.all(), many=True).data)
    serializer = HomeFloorSerializer(data=request.data)
    if not serializer.is_valid():
        return fail(next(iter(serializer.errors.values()))[0])
    serializer.save()
    return ok(serializer.data, "楼层已创建", 201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsConsole])
def floor_detail(request, pk):
    floor = HomeFloor.objects.filter(pk=pk).first()
    if not floor:
        return fail("楼层不存在", 40404, 404)
    if request.method == "DELETE":
        floor.delete()
        return ok(None, "楼层已删除")
    for field in ("name", "subtitle", "category", "tabs", "color", "enabled", "sort"):
        if field in request.data:
            setattr(floor, field, request.data[field])
    floor.save()
    return ok(HomeFloorSerializer(floor).data, "楼层已更新")


@api_view(["GET", "POST"])
@permission_classes([IsConsole])
def notices(request):
    if request.method == "GET":
        return ok(NoticeSerializer(Notice.objects.all(), many=True).data)
    serializer = NoticeSerializer(data=request.data)
    if not serializer.is_valid():
        return fail(next(iter(serializer.errors.values()))[0])
    serializer.save()
    return ok(serializer.data, "快报已创建", 201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsConsole])
def notice_detail(request, pk):
    notice = Notice.objects.filter(pk=pk).first()
    if not notice:
        return fail("快报不存在", 40404, 404)
    if request.method == "DELETE":
        notice.delete()
        return ok(None, "快报已删除")
    for field in ("title", "category", "enabled", "sort"):
        if field in request.data:
            setattr(notice, field, request.data[field])
    notice.save()
    return ok(NoticeSerializer(notice).data, "快报已更新")


# ---------------------------------------------------------------- 用户 / 优惠券


@api_view(["GET"])
@permission_classes([IsConsole])
def users(request):
    qs = User.objects.all()
    params = request.query_params
    if params.get("role"):
        qs = qs.filter(role=params["role"])
    if params.get("q"):
        qs = qs.filter(username__icontains=params["q"])
    return ok(paginate(qs, request, UserSerializer, default_size=10))


@api_view(["POST"])
@permission_classes([IsConsole])
def user_toggle(request, pk):
    user = User.objects.filter(pk=pk).first()
    if not user:
        return fail("用户不存在", 40404, 404)
    if user.role == "console":
        return fail("不能禁用平台账号")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    return ok(
        {"id": user.id, "is_active": user.is_active}, "已启用" if user.is_active else "已禁用"
    )


@api_view(["GET", "POST"])
@permission_classes([IsConsole])
def coupons(request):
    if request.method == "GET":
        return ok(
            [
                {
                    "id": c.id,
                    "name": c.name,
                    "amount": str(c.amount),
                    "threshold": str(c.threshold),
                    "total": c.total,
                    "claimed": c.claimed,
                    "scope": c.scope,
                    "valid_until": c.valid_until.strftime("%Y-%m-%d"),
                    "enabled": c.enabled,
                }
                for c in Coupon.objects.all()
            ]
        )
    try:
        Coupon.objects.create(
            name=request.data.get("name", "平台券"),
            amount=Decimal(str(request.data.get("amount", 10))),
            threshold=Decimal(str(request.data.get("threshold", 99))),
            total=int(request.data.get("total", 1000)),
            scope=request.data.get("scope", "全场通用"),
            valid_until=timezone.now() + timedelta(days=int(request.data.get("days", 30))),
        )
    except Exception:
        return fail("优惠券参数不正确")
    return ok(None, "优惠券已创建", 201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsConsole])
def coupon_detail(request, pk):
    coupon = Coupon.objects.filter(pk=pk).first()
    if not coupon:
        return fail("优惠券不存在", 40404, 404)
    if request.method == "DELETE":
        coupon.delete()
        return ok(None, "优惠券已删除")
    if "enabled" in request.data:
        coupon.enabled = bool(request.data["enabled"])
        coupon.save(update_fields=["enabled"])
    return ok(None, "已更新")
