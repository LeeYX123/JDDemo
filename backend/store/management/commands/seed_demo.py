"""生成可重复执行（幂等）的演示数据。

规模：8 个一级类目 / 每类 3 个二级 / 每二级 2 个三级 = 48 个叶子类目；
150 个 SPU、350+ SKU、12 个品牌、8 家店铺、20 笔历史订单、450+ 条评价。
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from store.models import (
    Address,
    AfterSale,
    Banner,
    Brand,
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

from ._seed_data import (
    BRAND_NAMES,
    CATEGORY_TREE,
    COLORS,
    COUPON_DEFS,
    REVIEW_TEXTS,
    SERIES,
    SHOP_DEFS,
    R,
)


class Command(BaseCommand):
    help = "生成京东演示数据（幂等，已存在则跳过）"

    def handle(self, *args, **options):
        if Spu.objects.exists():
            self.stdout.write(self.style.WARNING("演示数据已存在，跳过 seed_demo"))
            return

        now = timezone.now()
        buyer = User.objects.create_user(
            username="13800138000",
            password="123456",
            phone="13800138000",
            role="buyer",
            nickname="京东会员_8000",
            first_name="演示买家",
        )
        merchant = User.objects.create_user(
            username="13900139000",
            password="123456",
            phone="13900139000",
            role="merchant",
            nickname="星野旗舰店",
            first_name="演示商家",
        )
        User.objects.create_user(
            username="13700137000",
            password="123456",
            phone="13700137000",
            role="console",
            nickname="平台运营",
            first_name="平台管理员",
            is_staff=True,
        )
        buyers = [buyer]
        for i in range(1, 25):
            buyers.append(
                User.objects.create_user(
                    username=f"1380013{8000 + i}",
                    password="123456",
                    phone=f"1380013{8000 + i}",
                    role="buyer",
                    nickname=f"京东用户{8000 + i}",
                )
            )

        Address.objects.create(
            user=buyer,
            receiver="李明",
            phone="13800138000",
            province="北京市",
            city="北京市",
            district="朝阳区",
            detail="建国路 88 号京东大厦 A 座 12 层",
            tag="公司",
            is_default=True,
        )
        Address.objects.create(
            user=buyer,
            receiver="李小雨",
            phone="13800138001",
            province="上海市",
            city="上海市",
            district="浦东新区",
            detail="张江路 66 号 3 号楼 502",
            tag="家",
        )

        # ---------------- 类目
        leaf_list = []
        for i, (root_name, seconds) in enumerate(CATEGORY_TREE.items()):
            root = Category.objects.create(name=root_name, level=1, sort=i, icon="▦")
            for j, (second_name, leaves) in enumerate(seconds.items()):
                second = Category.objects.create(name=second_name, parent=root, level=2, sort=j)
                for k, (leaf_name, _titles, _price) in enumerate(leaves):
                    leaf = Category.objects.create(name=leaf_name, parent=second, level=3, sort=k)
                    leaf_list.append((root, second, leaf, leaves[k]))

        # ---------------- 品牌 / 店铺
        brands = [
            Brand.objects.create(name=name, first_letter=R.choice("ABCDEFGHIJKLMN"))
            for name in BRAND_NAMES
        ]
        shops = []
        for idx, (shop_name, brand_name) in enumerate(SHOP_DEFS):
            owner = (
                merchant
                if idx == 0
                else User.objects.create_user(
                    username=f"1390013{9000 + idx}",
                    password="123456",
                    phone=f"1390013{9000 + idx}",
                    role="merchant",
                    nickname=shop_name,
                )
            )
            shops.append(
                Shop.objects.create(
                    owner=owner,
                    name=shop_name,
                    rating=Decimal("4.9") if idx < 3 else Decimal("4.7"),
                    description=f"{brand_name}品牌官方直营，正品保障，全国联保。",
                    approved=True,
                )
            )

        # ---------------- 商品
        spu_index = 0
        for leaf_index, (_root, second, leaf, meta) in enumerate(leaf_list):
            _leaf_name, titles, (low, high) = meta
            for n in range(3):
                spu_index += 1
                brand = brands[(leaf_index * 3 + n) % len(brands)]
                shop = shops[(leaf_index + n) % len(shops)]
                base_title = titles[n % len(titles)]
                title = f"{brand.name} {R.choice(SERIES)} {base_title} {COLORS[(leaf_index + n) % len(COLORS)]}"
                if n == 2:
                    title = (
                        f"{brand.name} {base_title} 官方标配 {COLORS[(spu_index) % len(COLORS)]}"
                    )
                price = Decimal(R.randrange(low, high, 10))
                if price > 5000:
                    price = price - Decimal(R.randrange(0, 500, 50))
                spu = Spu.objects.create(
                    title=title,
                    subtitle=f"{second.name} · {leaf.name} · 京东物流 次日达",
                    category=leaf,
                    brand=brand,
                    shop=shop,
                    image_seed=spu_index,
                    tags="|".join(R.sample(["自营", "新品", "热销", "包邮", "plus", "秒杀"], k=3)),
                    sales=R.randrange(60, 6000),
                    review_count=0,
                    rating=Decimal(str(round(R.uniform(4.5, 5.0), 1))),
                    status="pending" if spu_index in (37, 88, 129) else "on",
                    detail=(
                        f"【{brand.name}官方旗舰】{title}。\n"
                        f"精选材质，做工细致，经过多道质检流程；支持 7 天无理由退货，"
                        f"全国联保，京东物流配送，部分区域次日达。"
                    ),
                )
                sku_count = 3 if spu_index <= 50 else 2
                for s in range(sku_count):
                    specs = {
                        "颜色": COLORS[(leaf_index + n + s) % len(COLORS)],
                        "版本": ["标准版", "升级版", "尊享版"][s],
                    }
                    Sku.objects.create(
                        spu=spu,
                        name=f"{specs['颜色']} {specs['版本']}",
                        specs=specs,
                        price=price + Decimal(s * R.choice([100, 200, 300])),
                        market_price=(price + Decimal(s * 200)) * Decimal("1.30"),
                        stock=R.randrange(20, 500),
                        image_seed=spu.image_seed,
                    )
                for r in range(3):
                    Review.objects.create(
                        spu=spu,
                        user=R.choice(buyers),
                        rating=R.choice([4, 5, 5, 5]),
                        content=REVIEW_TEXTS[(spu_index + r) % len(REVIEW_TEXTS)],
                        order_no="",
                    )
                spu.review_count = R.randrange(20, 900)
                spu.save(update_fields=["review_count"])

        # ---------------- 首页内容
        banners = [
            ("春日焕新季", "满 99 减 20 · 品质生活安心之选", "#ffe6e3", "/search?q=焕新"),
            ("百亿补贴 低至五折", "大牌好物，天天低价", "#fff1d6", "/search?q=补贴"),
            ("PLUS 会员专享", "限时抢购，全年省心", "#e3f1ff", "/coupons"),
            ("家电以旧换新", "最高补贴 2000 元", "#e7f7e9", "/search?q=家电"),
            ("手机新品首发", "以旧换新再减 300", "#f0e9ff", "/search?q=手机"),
            ("京东超市 次日达", "米面粮油一站购齐", "#ffeede", "/search?q=超市"),
        ]
        for i, (title, subtitle, color, link) in enumerate(banners):
            Banner.objects.create(
                title=title, subtitle=subtitle, color=color, image_seed=i + 1, link=link, sort=i
            )
        notices = [
            ("京东物流：全国 90% 区县次日达", "服务"),
            ("新人首单立减 10 元，叠加优惠券更划算", "优惠"),
            ("PLUS 会员专享价已上线，全年可省 2000 元", "活动"),
            ("家电以旧换新补贴最高 2000 元", "活动"),
            ("7 天无理由退货，售后无忧", "服务"),
            ("春季美妆节：满 199 减 50", "快报"),
        ]
        for i, (title, category) in enumerate(notices):
            Notice.objects.create(title=title, category=category, sort=i)
        floor_defs = [
            ("1F 手机通讯", "影像旗舰 · 5G 新品", "手机通讯"),
            ("2F 家用电器", "大家电 · 以旧换新", "大家电"),
            ("3F 电脑办公", "轻薄本 · 高效办公", "电脑整机"),
            ("4F 品质生活", "家纺厨具 · 焕新好物", "家纺"),
        ]
        for i, (name, subtitle, category_name) in enumerate(floor_defs):
            category = Category.objects.filter(name=category_name).first()
            HomeFloor.objects.create(
                name=name,
                subtitle=subtitle,
                category=category,
                tabs=["热门推荐", "新品上架", "价格亲民"],
                sort=i,
                color=["#e1251b", "#2f6bd8", "#0f9d8a", "#b45309"][i],
            )

        # ---------------- 秒杀
        activity = SeckillActivity.objects.create(
            name="京东秒杀",
            label="10:00 场",
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=5),
        )
        seckill_skus = list(Sku.objects.select_related("spu").order_by("-spu__sales")[:8])
        for sku in seckill_skus:
            SeckillItem.objects.create(
                activity=activity,
                sku=sku,
                seckill_price=(sku.price * Decimal("0.82")).quantize(Decimal("0.01")),
                limit_stock=120,
                sold=R.randrange(20, 100),
            )

        # ---------------- 优惠券
        for name, amount, threshold, total, scope in COUPON_DEFS:
            Coupon.objects.create(
                name=name,
                amount=Decimal(amount),
                threshold=Decimal(threshold),
                total=total,
                claimed=R.randrange(100, 900),
                scope=scope,
                valid_until=now + timedelta(days=R.randrange(15, 60)),
            )

        # ---------------- 历史订单（覆盖五种状态，均匀铺在近两周）
        status_plan = (
            ["pending_pay"] * 3
            + ["paid"] * 4
            + ["shipped"] * 4
            + ["completed"] * 6
            + ["cancelled"] * 2
            + ["aftersale"] * 1
        )
        day_plan = [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13]
        all_skus = list(Sku.objects.select_related("spu__shop").order_by("id"))
        shop0_skus = [s for s in all_skus if s.spu.shop_id == shops[0].id][:40]
        for i, status in enumerate(status_plan):
            owner = buyer if i % 3 != 2 else R.choice(buyers)
            prefer_own = i % 2 == 0 or status == "aftersale"
            chosen = R.sample(shop0_skus if prefer_own else all_skus, k=1 if i % 3 else 2)
            quantity = 2 if i % 5 == 0 else 1
            subtotal = sum((s.price * quantity for s in chosen), Decimal("0"))
            freight = Decimal("0") if subtotal >= 99 else Decimal("8")
            created = now - timedelta(
                days=day_plan[i % len(day_plan)],
                hours=R.randrange(0, 12),
                minutes=R.randrange(0, 60),
            )
            order = Order.objects.create(
                order_no=f"O{created.strftime('%Y%m%d%H%M%S')}{i:03d}",
                batch_no=f"B{created.strftime('%Y%m%d')}{i:03d}",
                user=owner,
                address=owner.addresses.first() or Address.objects.filter(user=buyer).first(),
                address_snapshot={
                    "receiver": "李明",
                    "phone": "13800138000",
                    "full_text": "北京市北京市朝阳区 建国路 88 号京东大厦 A 座 12 层",
                },
                status=status,
                subtotal=subtotal,
                freight=freight,
                total=subtotal + freight,
                remark="" if i % 4 else "请放前台，谢谢",
                tracking_no=f"JDVA{i:08d}" if status in ("shipped", "completed") else "",
            )
            item = None
            for sku in chosen:
                item = OrderItem.objects.create(
                    order=order,
                    sku=sku,
                    shop=sku.spu.shop,
                    title_snapshot=sku.spu.title,
                    specs_snapshot=sku.specs,
                    price_snapshot=sku.price,
                    quantity=quantity,
                    image_seed=sku.spu.image_seed,
                )
            if status in ("paid", "shipped", "completed", "aftersale"):
                order.paid_at = created + timedelta(minutes=12)
            if status in ("shipped", "completed"):
                order.shipped_at = created + timedelta(hours=6)
            if status == "completed":
                order.completed_at = created + timedelta(days=2)
            order.created_at = created
            order.save()
            Order.objects.filter(pk=order.pk).update(created_at=created)
            if status == "aftersale" and item:
                AfterSale.objects.create(
                    order_item=item,
                    user=order.user,
                    type="refund",
                    reason="商品与描述不符",
                    description="收到后发现颜色与页面不一致，申请退款。",
                    amount=item.price_snapshot * item.quantity,
                    status="pending",
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"seed 完成：类目 {Category.objects.count()} / 品牌 {Brand.objects.count()} / "
                f"店铺 {Shop.objects.count()} / SPU {Spu.objects.count()} / SKU {Sku.objects.count()} / "
                f"评价 {Review.objects.count()} / 订单 {Order.objects.count()}"
            )
        )
