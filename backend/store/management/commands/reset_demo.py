from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "清空全部业务数据并重新生成演示数据（恢复初始状态）"

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="跳过确认提示")

    def handle(self, *args, **options):
        if not options["yes"]:
            self.stdout.write(
                self.style.WARNING("该操作会清空数据库全部数据，请追加 --yes 确认执行")
            )
            return
        call_command("flush", interactive=False, verbosity=0)
        self.stdout.write("数据库已清空，开始重建演示数据…")
        call_command("seed_demo")
        self.stdout.write(self.style.SUCCESS("reset_demo 完成"))
