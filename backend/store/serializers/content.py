"""内容运营类序列化：轮播、快报、楼层、优惠券、秒杀。"""

from rest_framework import serializers

from ..models import (
    Banner,
    Coupon,
    HomeFloor,
    Notice,
    SeckillActivity,
    SeckillItem,
)


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "color", "image_seed", "link", "enabled", "sort"]


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ["id", "title", "category", "enabled", "sort"]


class HomeFloorSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default="")

    class Meta:
        model = HomeFloor
        fields = [
            "id",
            "name",
            "subtitle",
            "category",
            "category_name",
            "tabs",
            "color",
            "enabled",
            "sort",
        ]


class CouponSerializer(serializers.ModelSerializer):
    claimed_by_me = serializers.SerializerMethodField()
    valid_until = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = Coupon
        fields = [
            "id",
            "name",
            "amount",
            "threshold",
            "total",
            "claimed",
            "scope",
            "valid_until",
            "enabled",
            "claimed_by_me",
        ]

    def get_claimed_by_me(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.users.filter(id=request.user.id).exists()
        return False


class SeckillItemSerializer(serializers.ModelSerializer):
    spu_id = serializers.IntegerField(source="sku.spu_id", read_only=True)
    sku_id = serializers.IntegerField(source="sku.id", read_only=True)
    title = serializers.CharField(source="sku.spu.title", read_only=True)
    image_seed = serializers.IntegerField(source="sku.spu.image_seed", read_only=True)
    price = serializers.DecimalField(
        source="sku.price", max_digits=10, decimal_places=2, read_only=True
    )
    market_price = serializers.DecimalField(
        source="sku.market_price", max_digits=10, decimal_places=2, read_only=True
    )
    spec = serializers.CharField(source="sku.name", read_only=True)

    class Meta:
        model = SeckillItem
        fields = [
            "id",
            "spu_id",
            "sku_id",
            "title",
            "image_seed",
            "price",
            "market_price",
            "spec",
            "seckill_price",
            "limit_stock",
            "sold",
        ]


class SeckillActivitySerializer(serializers.ModelSerializer):
    items = SeckillItemSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = SeckillActivity
        fields = ["id", "name", "label", "start_at", "end_at", "enabled", "items", "status"]

    def get_status(self, obj):
        from django.utils import timezone

        now = timezone.now()
        if now < obj.start_at:
            return "upcoming"
        if now > obj.end_at:
            return "ended"
        return "running"
