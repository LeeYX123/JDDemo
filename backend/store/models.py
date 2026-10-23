"""京东演示项目数据模型。

金额统一 Decimal(10, 2)，订单商品保存标题/规格/价格快照，
订单状态集中在本文件的 Order.STATUS 中管理。
"""

from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """买家 / 商家 / 平台三种角色共用一张用户表，username 即手机号。"""

    ROLE_CHOICES = (("buyer", "买家"), ("merchant", "商家"), ("console", "平台"))
    username = models.CharField("手机号", max_length=32, unique=True)
    nickname = models.CharField(max_length=40, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="buyer")
    avatar = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date_joined"]

    @property
    def display_name(self):
        return self.nickname or self.first_name or self.username

    def __str__(self):
        return f"{self.username}({self.get_role_display()})"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    receiver = models.CharField(max_length=40)
    phone = models.CharField(max_length=20)
    province = models.CharField(max_length=30)
    city = models.CharField(max_length=30)
    district = models.CharField(max_length=30)
    detail = models.CharField(max_length=120)
    tag = models.CharField(max_length=12, blank=True, default="家")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-id"]

    @property
    def full_text(self):
        return f"{self.province}{self.city}{self.district} {self.detail}"

    def __str__(self):
        return f"{self.receiver} {self.full_text}"


class Category(models.Model):
    """三级自关联类目。level: 1/2/3。"""

    name = models.CharField(max_length=40)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    level = models.PositiveSmallIntegerField(default=1)
    icon = models.CharField(max_length=20, blank=True, default="▦")
    enabled = models.BooleanField(default=True)
    sort = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["level", "sort", "id"]
        indexes = [models.Index(fields=["parent", "enabled"])]

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=60, unique=True)
    logo = models.CharField(max_length=255, blank=True)
    first_letter = models.CharField(max_length=1, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["first_letter", "id"]

    def __str__(self):
        return self.name


class Shop(models.Model):
    owner = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="shops"
    )
    name = models.CharField(max_length=80)
    logo = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=200, blank=True, default="京东品质 · 正品保障")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal("4.8"))
    approved = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Spu(models.Model):
    STATUS = (
        ("draft", "草稿"),
        ("pending", "待审核"),
        ("on", "在售"),
        ("off", "下架"),
        ("rejected", "审核驳回"),
    )
    title = models.CharField(max_length=180)
    subtitle = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="spus")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="spus")
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="spus")
    image_seed = models.PositiveIntegerField(default=1)
    tags = models.CharField(max_length=255, blank=True)
    services = models.CharField(max_length=255, blank=True, default="京东物流|七天无理由|正品保障")
    sales = models.PositiveIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal("4.9"))
    status = models.CharField(max_length=12, choices=STATUS, default="on")
    reject_reason = models.CharField(max_length=200, blank=True)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-sales", "-id"]
        indexes = [models.Index(fields=["status", "category"])]

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        return [t for t in self.tags.split("|") if t]

    @property
    def service_list(self):
        return [t for t in self.services.split("|") if t]


class Sku(models.Model):
    spu = models.ForeignKey(Spu, on_delete=models.CASCADE, related_name="skus")
    name = models.CharField(max_length=120)
    specs = models.JSONField(default=dict)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    market_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=100)
    image_seed = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["price", "id"]

    def __str__(self):
        return f"{self.spu.title} / {self.name}"


class Review(models.Model):
    spu = models.ForeignKey(Spu, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    order_no = models.CharField(max_length=32, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    content = models.TextField()
    images = models.JSONField(default=list, blank=True)
    reply = models.CharField(max_length=255, blank=True, default="感谢您的认可，我们会继续努力！")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.spu.title} {self.rating}星"


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    sku = models.ForeignKey(Sku, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    selected = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "sku"], name="uniq_cart_user_sku")]
        ordering = ["-id"]


class Order(models.Model):
    STATUS = (
        ("pending_pay", "等待付款"),
        ("paid", "等待发货"),
        ("shipped", "等待收货"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
        ("aftersale", "售后中"),
        ("refunded", "已退款"),
    )
    STATUS_FLOW = ["pending_pay", "paid", "shipped", "completed"]
    order_no = models.CharField(max_length=32, unique=True)
    batch_no = models.CharField(max_length=32, blank=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    address = models.ForeignKey(Address, null=True, on_delete=models.SET_NULL)
    address_snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending_pay")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pay_method = models.CharField(max_length=20, blank=True, default="")
    remark = models.CharField(max_length=255, blank=True)
    cancel_reason = models.CharField(max_length=120, blank=True)
    tracking_no = models.CharField(max_length=60, blank=True)
    tracking_company = models.CharField(max_length=40, blank=True, default="京东物流")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return self.order_no

    @property
    def shops(self):
        seen = []
        for item in self.items.all():
            if item.shop and item.shop not in seen:
                seen.append(item.shop)
        return seen


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    sku = models.ForeignKey(Sku, null=True, on_delete=models.SET_NULL)
    shop = models.ForeignKey(Shop, null=True, on_delete=models.SET_NULL)
    title_snapshot = models.CharField(max_length=180)
    specs_snapshot = models.JSONField(default=dict)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    image_seed = models.PositiveIntegerField(default=1)
    reviewed = models.BooleanField(default=False)

    @property
    def amount(self):
        return self.price_snapshot * self.quantity


class AfterSale(models.Model):
    STATUS = (
        ("pending", "审核中"),
        ("approved", "已同意"),
        ("rejected", "已驳回"),
        ("refunded", "已退款"),
    )
    TYPES = (("refund", "仅退款"), ("return", "退货退款"))
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="aftersales")
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="aftersales")
    type = models.CharField(max_length=12, choices=TYPES, default="refund")
    reason = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reply = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    handled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_item.title_snapshot} {self.get_status_display()}"


class Banner(models.Model):
    title = models.CharField(max_length=80)
    subtitle = models.CharField(max_length=160, blank=True)
    color = models.CharField(max_length=20, default="#ffe7e5")
    image_seed = models.PositiveIntegerField(default=1)
    link = models.CharField(max_length=255, blank=True, default="/search")
    enabled = models.BooleanField(default=True)
    sort = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort", "id"]


class Notice(models.Model):
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=30, default="快报")
    enabled = models.BooleanField(default=True)
    sort = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort", "id"]


class HomeFloor(models.Model):
    name = models.CharField(max_length=60)
    subtitle = models.CharField(max_length=120, blank=True)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    tabs = models.JSONField(default=list, blank=True)
    color = models.CharField(max_length=20, default="#e1251b")
    enabled = models.BooleanField(default=True)
    sort = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort", "id"]


class SeckillActivity(models.Model):
    name = models.CharField(max_length=80)
    label = models.CharField(max_length=20, default="10:00 场")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_at"]


class SeckillItem(models.Model):
    activity = models.ForeignKey(SeckillActivity, on_delete=models.CASCADE, related_name="items")
    sku = models.ForeignKey(Sku, on_delete=models.CASCADE)
    seckill_price = models.DecimalField(max_digits=10, decimal_places=2)
    limit_stock = models.PositiveIntegerField(default=100)
    sold = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]


class Coupon(models.Model):
    name = models.CharField(max_length=80)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.PositiveIntegerField(default=1000)
    claimed = models.PositiveIntegerField(default=0)
    scope = models.CharField(max_length=40, blank=True, default="全场通用")
    valid_until = models.DateTimeField()
    enabled = models.BooleanField(default=True)
    users = models.ManyToManyField(User, blank=True, related_name="coupons")

    class Meta:
        ordering = ["threshold", "-amount"]

    def __str__(self):
        return self.name
