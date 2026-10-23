"""按 backend/.env 的连接信息创建 MySQL 数据库（幂等）。

仅在 DB_ENGINE=mysql 时由 start 脚本调用；sqlite 模式直接跳过。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "backend" / ".env"


def read_env():
    values = {}
    if not ENV_FILE.exists():
        return values
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main():
    env = read_env()
    engine = env.get("DB_ENGINE", "sqlite").lower()
    if engine != "mysql":
        print(f"[skip] DB_ENGINE={engine}，无需创建 MySQL 数据库")
        return 0

    name = env.get("DB_NAME", "jdshop")
    user = env.get("DB_USER", "root")
    password = env.get("DB_PASSWORD", "")
    host = env.get("DB_HOST", "127.0.0.1")
    port = int(env.get("DB_PORT", "3306") or 3306)

    if not password:
        print("[error] backend/.env 里 DB_PASSWORD 为空，请填写 MySQL 密码后重新运行")
        return 2

    try:
        import pymysql
    except ImportError:
        print("[error] 缺少 PyMySQL，请先执行 pip install -r requirements.txt")
        return 3

    try:
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password, charset="utf8mb4"
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[error] 连接 MySQL 失败：{exc}")
        print("        请确认 MySQL 已启动，且 .env 中的 DB_USER / DB_PASSWORD 正确")
        return 4

    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{name}` DEFAULT CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    print(f"[ok] 数据库 {name} 已就绪（utf8mb4）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
