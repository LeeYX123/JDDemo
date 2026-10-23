"""Django Admin 注册（后台主要走自建 admin SPA，这里仅用于本地调试数据）。"""

from django.contrib import admin

from .models import (
    Address,
    AfterSale,
    Banner,
    Brand,
    CartItem,
    Category,
    Coupon,
    HomeFloor,
    Notice,
    Order,
    OrderItem,
    Review,
    SeckillActivity,
    SeckillItem,
    Shop,
    Sku,
    Spu,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "nickname", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("username", "nickname")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "parent", "enabled", "sort")
    list_filter = ("level", "enabled")


@admin.register(Spu)
class SpuAdmin(admin.ModelAdmin):
    list_display = ("title", "shop", "category", "status", "sales")
    list_filter = ("status", "shop")
    search_fields = ("title",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "user", "status", "total", "created_at")
    list_filter = ("status",)
    search_fields = ("order_no",)


for model in [
    Address,
    Brand,
    Shop,
    Sku,
    Review,
    CartItem,
    OrderItem,
    AfterSale,
    Banner,
    Notice,
    HomeFloor,
    SeckillActivity,
    SeckillItem,
    Coupon,
]:
    admin.site.register(model)
