"""目录类序列化：用户、类目、品牌、店铺、SKU、商品、评价。"""

from rest_framework import serializers

from ..models import Brand, Category, Review, Shop, Sku, Spu, User


class UserSerializer(serializers.ModelSerializer):
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    nickname = serializers.CharField(required=False, allow_blank=True)
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "nickname",
            "phone",
            "role",
            "role_label",
            "avatar",
            "email",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["is_active", "date_joined"]


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "parent",
            "level",
            "enabled",
            "sort",
            "icon",
            "children",
            "product_count",
        ]

    def get_children(self, obj):
        children = list(obj.children.all())
        if not self.context.get("include_disabled"):
            children = [c for c in children if c.enabled]
        return CategorySerializer(children, many=True, context=self.context).data

    def get_product_count(self, obj):
        if obj.level == 3:
            return obj.spus.filter(status="on").count()
        if obj.level == 2:
            return Spu.objects.filter(category__parent=obj, status="on").count()
        return Spu.objects.filter(category__parent__parent=obj, status="on").count()


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "logo", "first_letter", "enabled"]


class ShopSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.username", read_only=True, default="")

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "logo",
            "rating",
            "description",
            "approved",
            "enabled",
            "owner_name",
        ]


class SkuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sku
        fields = ["id", "name", "specs", "price", "market_price", "stock", "image_seed", "enabled"]


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    avatar_seed = serializers.SerializerMethodField()
    specs = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "rating",
            "content",
            "images",
            "reply",
            "created_at",
            "user_name",
            "avatar_seed",
            "specs",
            "order_no",
        ]

    def get_user_name(self, obj):
        if not obj.user:
            return "京东用户"
        name = obj.user.nickname or obj.user.username
        return name[:3] + "****" if len(name) > 3 else name

    def get_avatar_seed(self, obj):
        return (obj.user_id or 1) % 8

    def get_specs(self, obj):
        return ""


class ProductListSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    shop_id = serializers.IntegerField(source="shop.id", read_only=True)
    brand_id = serializers.IntegerField(source="brand.id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_id = serializers.IntegerField(source="category.id", read_only=True)
    price = serializers.SerializerMethodField()
    market_price = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    tag_list = serializers.SerializerMethodField()

    class Meta:
        model = Spu
        fields = [
            "id",
            "title",
            "subtitle",
            "brand_name",
            "brand_id",
            "shop_name",
            "shop_id",
            "category_name",
            "category_id",
            "price",
            "market_price",
            "stock",
            "sales",
            "review_count",
            "rating",
            "image_seed",
            "tags",
            "tag_list",
            "services",
            "status",
        ]

    def _skus(self, obj):
        return list(obj.skus.all())

    def get_price(self, obj):
        skus = self._skus(obj)
        return str(min((s.price for s in skus), default=0))

    def get_market_price(self, obj):
        skus = self._skus(obj)
        return str(max((s.market_price for s in skus), default=0))

    def get_stock(self, obj):
        return sum(s.stock for s in self._skus(obj))

    def get_tag_list(self, obj):
        return obj.tag_list


class ProductDetailSerializer(ProductListSerializer):
    skus = SkuSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    shop = ShopSerializer(read_only=True)
    category_path = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            "detail",
            "skus",
            "reviews",
            "shop",
            "category_path",
            "service_list",
            "created_at",
        ]

    def get_reviews(self, obj):
        qs = obj.reviews.all()[:20]
        return ReviewSerializer(qs, many=True).data

    def get_category_path(self, obj):
        path, node = [], obj.category
        while node:
            path.append({"id": node.id, "name": node.name})
            node = node.parent
        return list(reversed(path))
