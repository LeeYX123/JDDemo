from django.contrib.auth import authenticate
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from ..models import Address, Coupon, Order, Shop, User
from ..responses import fail, ok
from ..serializers import UserSerializer


def token_data(user, with_refresh=True):
    refresh = RefreshToken.for_user(user)
    data = {
        "access": str(refresh.access_token),
        "user": UserSerializer(user).data,
    }
    if with_refresh:
        data["refresh"] = str(refresh)
    return data


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = str(request.data.get("username", "")).strip()
    password = request.data.get("password", "")
    if not username or not password:
        return fail("请输入手机号和密码", 40001)
    user = authenticate(username=username, password=password)
    if not user:
        return fail("手机号或密码错误", 40101, 401)
    if not user.is_active:
        return fail("账号已被禁用，请联系平台", 40301, 403)
    return ok(token_data(user), "登录成功")


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = str(request.data.get("username", "")).strip()
    password = str(request.data.get("password", ""))
    if request.data.get("captcha") != "8888":
        return fail("验证码错误（演示验证码固定为 8888）", 40002)
    if len(username) != 11 or not username.isdigit():
        return fail("请输入 11 位手机号", 40003)
    if len(password) < 6:
        return fail("密码至少 6 位", 40003)
    if User.objects.filter(username=username).exists():
        return fail("该手机号已注册", 40004)
    user = User.objects.create_user(
        username=username,
        password=password,
        phone=username,
        nickname=str(request.data.get("nickname", "")) or f"京东用户{username[-4:]}",
        role="buyer",
    )
    return ok(token_data(user), "注册成功", 201)


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh(request):
    token = request.data.get("refresh", "")
    try:
        refresh_token = RefreshToken(token)
        return ok({"access": str(refresh_token.access_token)}, "已刷新")
    except TokenError:
        return fail("登录已过期，请重新登录", 40102, 401)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == "PATCH":
        user = request.user
        for field in ("nickname", "phone", "email", "avatar"):
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
    shop = Shop.objects.filter(owner=request.user).first()
    data = UserSerializer(request.user).data
    data["shop"] = {"id": shop.id, "name": shop.name} if shop else None
    return ok(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    """个人中心顶部统计与订单角标。"""
    orders = Order.objects.filter(user=request.user)
    counts = {row["status"]: row["n"] for row in orders.values("status").annotate(n=Count("id"))}
    return ok(
        {
            "order_counts": counts,
            "pending_pay": counts.get("pending_pay", 0),
            "pending_ship": counts.get("paid", 0),
            "pending_receive": counts.get("shipped", 0),
            "after_sale": counts.get("aftersale", 0),
            "addresses": Address.objects.filter(user=request.user).count(),
            "coupons": Coupon.objects.filter(users=request.user).count(),
            "user": UserSerializer(request.user).data,
        }
    )
