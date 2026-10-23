from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ..models import CartItem, Sku
from ..responses import fail, ok
from ..serializers import CartSerializer


def cart_data(user):
    items = (
        CartItem.objects.filter(user=user)
        .select_related("sku__spu__shop")
        .order_by("sku__spu__shop_id", "-id")
    )
    return CartSerializer(items, many=True).data


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def cart(request):
    if request.method == "GET":
        return ok(cart_data(request.user))

    if request.method == "DELETE":
        CartItem.objects.filter(user=request.user, selected=True).delete()
        return ok(cart_data(request.user), "已删除选中商品")

    sku_id = request.data.get("sku_id")
    try:
        qty = max(1, int(request.data.get("quantity", 1)))
    except (TypeError, ValueError):
        qty = 1
    sku = Sku.objects.select_related("spu").filter(pk=sku_id, enabled=True).first()
    if not sku or sku.spu.status != "on":
        return fail("规格不存在或已下架", 40404, 404)
    if sku.stock <= 0:
        return fail("该规格暂时无货")
    item, created = CartItem.objects.get_or_create(
        user=request.user, sku=sku, defaults={"quantity": min(qty, sku.stock)}
    )
    if not created:
        item.quantity = min(sku.stock, item.quantity + qty)
        item.selected = True
        item.save(update_fields=["quantity", "selected"])
    return ok(cart_data(request.user), "已加入购物车")


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def cart_item(request, pk):
    item = CartItem.objects.filter(pk=pk, user=request.user).select_related("sku").first()
    if not item:
        return fail("购物车商品不存在", 40404, 404)
    if request.method == "DELETE":
        item.delete()
        return ok(cart_data(request.user), "已删除")
    if "quantity" in request.data:
        try:
            item.quantity = max(1, min(item.sku.stock, int(request.data["quantity"])))
        except (TypeError, ValueError):
            return fail("数量格式不正确")
    if "selected" in request.data:
        item.selected = bool(request.data["selected"])
    item.save()
    return ok(cart_data(request.user), "已更新")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cart_toggle(request):
    selected = bool(request.data.get("selected"))
    CartItem.objects.filter(user=request.user).update(selected=selected)
    return ok(cart_data(request.user), "已全选" if selected else "已取消全选")
