"""演示数据"保鲜"：把依赖时间的内容拨到当前时间窗口。

项目放置几天后再启动时，秒杀场次会过期、优惠券会失效、看板近 7 日趋势会全空。
本命令幂等，在每次启动时执行一次即可。
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from store.models import Coupon, Order, SeckillActivity


class Command(BaseCommand):
    help = "刷新演示数据的时间窗口（秒杀场次、优惠券有效期、历史订单日期）"

    def handle(self, *args, **options):
        now = timezone.now()
        notes = []

        activity = SeckillActivity.objects.filter(enabled=True).order_by("-start_at").first()
        if activity and activity.end_at < now:
            activity.start_at = now - timedelta(hours=1)
            activity.end_at = now + timedelta(hours=5)
            activity.save(update_fields=["start_at", "end_at"])
            notes.append("秒杀场次已顺延")

        expired = Coupon.objects.filter(enabled=True, valid_until__lt=now)
        count = expired.count()
        if count:
            expired.update(valid_until=now + timedelta(days=30))
            notes.append(f"{count} 张优惠券有效期已顺延")

        latest = Order.objects.order_by("-created_at").values_list("created_at", flat=True).first()
        if latest:
            days = (now.date() - timezone.localtime(latest).date()).days
            if days >= 3:
                for order in Order.objects.all():
                    order.created_at = order.created_at + timedelta(days=days)
                    if order.paid_at:
                        order.paid_at = order.paid_at + timedelta(days=days)
                    if order.shipped_at:
                        order.shipped_at = order.shipped_at + timedelta(days=days)
                    if order.completed_at:
                        order.completed_at = order.completed_at + timedelta(days=days)
                    order.save(
                        update_fields=["created_at", "paid_at", "shipped_at", "completed_at"]
                    )
                notes.append(f"历史订单整体顺延 {days} 天")

        if notes:
            self.stdout.write("演示数据保鲜：" + "，".join(notes))
        else:
            self.stdout.write("演示数据时间窗口正常")
