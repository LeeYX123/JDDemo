"""交易类序列化：购物车、地址、订单、订单项、售后。"""

from rest_framework import serializers

from ..models import Address, AfterSale, CartItem, Order, OrderItem


class CartSerializer(serializers.ModelSerializer):
    sku_name = serializers.CharField(source="sku.name", read_only=True)
    title = serializers.CharField(source="sku.spu.title", read_only=True)
    price = serializers.DecimalField(
        source="sku.price", max_digits=10, decimal_places=2, read_only=True
    )
    market_price = serializers.DecimalField(
        source="sku.market_price", max_digits=10, decimal_places=2, read_only=True
    )
    specs = serializers.JSONField(source="sku.specs", read_only=True)
    shop_id = serializers.IntegerField(source="sku.spu.shop_id", read_only=True)
    shop_name = serializers.CharField(source="sku.spu.shop.name", read_only=True)
    spu_id = serializers.IntegerField(source="sku.spu_id", read_only=True)
    image_seed = serializers.IntegerField(source="sku.spu.image_seed", read_only=True)
    stock = serializers.IntegerField(source="sku.stock", read_only=True)
    valid = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "sku",
            "sku_name",
            "title",
            "price",
            "market_price",
            "specs",
            "shop_id",
            "shop_name",
            "spu_id",
            "image_seed",
            "quantity",
            "selected",
            "stock",
            "valid",
        ]

    def get_valid(self, obj):
        return obj.sku.enabled and obj.sku.spu.status == "on" and obj.sku.stock > 0


class AddressSerializer(serializers.ModelSerializer):
    full_text = serializers.CharField(read_only=True)

    class Meta:
        model = Address
        fields = [
            "id",
            "receiver",
            "phone",
            "province",
            "city",
            "district",
            "detail",
            "tag",
            "is_default",
            "full_text",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source="shop.name", read_only=True, default="")
    shop_id = serializers.IntegerField(read_only=True)
    spu_id = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    aftersale_status = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "sku",
            "spu_id",
            "shop",
            "shop_id",
            "shop_name",
            "title_snapshot",
            "specs_snapshot",
            "price_snapshot",
            "quantity",
            "image_seed",
            "reviewed",
            "amount",
            "aftersale_status",
        ]

    def get_spu_id(self, obj):
        return obj.sku.spu_id if obj.sku else None

    def get_amount(self, obj):
        return str(obj.amount)

    def get_aftersale_status(self, obj):
        latest = obj.aftersales.order_by("-id").first()
        return latest.get_status_display() if latest else ""


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    shop_names = serializers.SerializerMethodField()
    can_pay = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_confirm = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "batch_no",
            "status",
            "status_label",
            "subtotal",
            "freight",
            "discount",
            "total",
            "remark",
            "tracking_no",
            "tracking_company",
            "address_snapshot",
            "created_at",
            "paid_at",
            "shipped_at",
            "completed_at",
            "items",
            "shop_names",
            "can_pay",
            "can_cancel",
            "can_confirm",
            "can_review",
        ]

    def get_shop_names(self, obj):
        names = []
        for item in obj.items.all():
            name = item.shop.name if item.shop else "京东自营"
            if name not in names:
                names.append(name)
        return names

    def get_can_pay(self, obj):
        return obj.status == "pending_pay"

    def get_can_cancel(self, obj):
        return obj.status == "pending_pay"

    def get_can_confirm(self, obj):
        return obj.status == "shipped"

    def get_can_review(self, obj):
        return obj.status == "completed" and not all(i.reviewed for i in obj.items.all())


class AfterSaleSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    type_label = serializers.CharField(source="get_type_display", read_only=True)
    order_no = serializers.CharField(source="order_item.order.order_no", read_only=True)
    title = serializers.CharField(source="order_item.title_snapshot", read_only=True)
    image_seed = serializers.IntegerField(source="order_item.image_seed", read_only=True)
    shop_name = serializers.SerializerMethodField()

    class Meta:
        model = AfterSale
        fields = [
            "id",
            "status",
            "status_label",
            "type",
            "type_label",
            "reason",
            "description",
            "amount",
            "reply",
            "created_at",
            "handled_at",
            "order_no",
            "title",
            "image_seed",
            "order_item",
            "shop_name",
        ]

    def get_shop_name(self, obj):
        return obj.order_item.shop.name if obj.order_item.shop else ""
