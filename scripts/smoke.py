"""端到端冒烟脚本：登录 -> 搜索 -> 详情 -> 加购 -> 结算 -> 支付 -> 发货 -> 收货 -> 评价 -> 售后 -> 平台处理。

用法（三服务已启动）：
    python scripts/smoke.py [--base http://127.0.0.1:8000]

只依赖标准库，不需要额外安装 requests。
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
TOKENS = {}
PASSED = 0
FAILED = 0


def call(method, path, data=None, token=None, expect=(200, 201), allow_error=False):
    url = f"{BASE}/api/v1{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.status
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        status = exc.code
        payload = json.loads(exc.read().decode() or "{}")
    except urllib.error.URLError as exc:
        check(False, f"{method} {path}", f"后端未启动？{exc.reason}")
        sys.exit(1)
    if status not in expect:
        check(False, f"{method} {path}", f"HTTP {status} {payload.get('msg', payload)}")
        return None
    if payload.get("code") != 0:
        if allow_error:
            return {"status": status, "payload": payload}
        check(False, f"{method} {path}", payload.get("msg", "业务失败"))
        return None
    return payload.get("data")


def check(ok, title, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {title}")
    else:
        FAILED += 1
        print(f"  [FAIL] {title}  {detail}")


def step(text):
    print(f"\n=== {text} ===")


def login(username, role):
    data = call("POST", "/auth/login/", {"username": username, "password": "123456"})
    if not data:
        check(False, f"{role} 登录", username)
        return None
    check(data["user"]["role"] == role, f"{role} 登录（{username}）")
    return data["access"]


def main():
    global BASE
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    BASE = parser.parse_args().base.rstrip("/")

    step("1. 认证")
    buyer = login("13800138000", "buyer")
    merchant = login("13900139000", "merchant")
    console = login("13700137000", "console")
    if not (buyer and merchant and console):
        summary()
        return 1

    step("2. 首页与搜索")
    home = call("GET", "/home/")
    check(bool(home["floors"]), f"首页楼层 {len(home['floors'])} 个")
    check(bool(home["seckill"] and home["seckill"]["items"]), "秒杀活动有商品")
    check(bool(home["guess"]), f"猜你喜欢 {len(home['guess'])} 个商品")
    search = call("GET", "/products/?q=%E6%89%8B%E6%9C%BA&page=1&size=8")
    check(search["total"] > 0, f"搜索「手机」命中 {search['total']} 个商品")
    filtered = call("GET", "/products/?category=3&min_price=100&max_price=9999&ordering=price_asc")
    prices = [float(item["price"]) for item in filtered["results"]]
    check(prices == sorted(prices), "价格升序排序生效")

    step("3. 商品详情与 SKU（选商家自有商品，便于后续发货）")
    shop = call("GET", "/merchant/shop/", token=merchant)
    own = call("GET", f"/products/?shop={shop['id']}&size=1&ordering=sales")
    pid = own["results"][0]["id"]
    detail = call("GET", f"/products/{pid}/")
    check(bool(detail["skus"]), f"详情含 {len(detail['skus'])} 个 SKU")
    check(bool(detail["reviews"]), f"详情含 {len(detail['reviews'])} 条评价")
    sku = detail["skus"][0]

    step("4. 购物车")
    call("POST", "/cart/toggle/", {"selected": True}, token=buyer)
    call("DELETE", "/cart/", token=buyer)
    cart = call("POST", "/cart/", {"sku_id": sku["id"], "quantity": 2}, token=buyer)
    check(bool(cart), "加入购物车成功")
    call("POST", "/cart/toggle/", {"selected": True}, token=buyer)
    cart = call("GET", "/cart/", token=buyer)
    row = next((item for item in cart if item["sku"] == sku["id"]), None)
    check(row is not None and row["quantity"] >= 2, "购物车数量正确")
    item_id = row["id"]
    cart = call("PATCH", f"/cart/{item_id}/", {"quantity": 2}, token=buyer)
    check(
        any(item["id"] == item_id and item["quantity"] == 2 for item in cart), "修改购物车数量生效"
    )

    stock_before = call("GET", f"/products/{pid}/")["stock"]

    step("5. 下单（按店铺拆单 + 满 99 免运费）")
    addresses = call("GET", "/addresses/", token=buyer)
    check(bool(addresses), f"地址簿 {len(addresses)} 条")
    order_data = call(
        "POST", "/orders/", {"address_id": addresses[0]["id"], "remark": "冒烟脚本"}, token=buyer
    )
    if not order_data:
        summary()
        return 1
    orders = order_data["orders"]
    check(len(orders) >= 1, f"生成 {len(orders)} 笔订单（批次 {order_data['batch_no']}）")
    order_no = orders[0]["order_no"]
    stock_after = call("GET", f"/products/{pid}/")["stock"]
    check(stock_after == stock_before - 2 * 1, f"库存扣减正确：{stock_before} -> {stock_after}")

    step("6. 支付")
    paid = call(
        "POST",
        "/payment/mock/",
        {"batch_no": order_data["batch_no"], "method": "mock"},
        token=buyer,
    )
    check(bool(paid), f"Mock 支付成功，{paid['paid']} 笔转待发货")
    detail = call("GET", f"/orders/{order_no}/", token=buyer)
    check(detail["status"] == "paid", "订单状态变为等待发货")

    step("7. 商家发货")
    shipped = call(
        "POST",
        f"/merchant/orders/{order_no}/ship/",
        {"tracking_no": "JDVA88889999", "tracking_company": "京东物流"},
        token=merchant,
    )
    check(bool(shipped) and shipped["status"] == "shipped", "发货成功并写入运单号")

    step("8. 买家确认收货")
    confirmed = call("POST", f"/orders/{order_no}/confirm/", token=buyer)
    check(bool(confirmed) and confirmed["status"] == "completed", "订单已完成")

    step("9. 评价")
    reviewed = call(
        "POST",
        "/reviews/",
        {"order_no": order_no, "rating": 5, "content": "冒烟脚本自动评价：物流快，包装好。"},
        token=buyer,
    )
    check(bool(reviewed), f"评价提交成功（{reviewed['count'] if reviewed else 0} 件）")

    step("10. 申请售后")
    detail = call("GET", f"/orders/{order_no}/", token=buyer)
    order_item_id = detail["items"][0]["id"]
    sale = call(
        "POST",
        "/aftersales/",
        {
            "order_item_id": order_item_id,
            "type": "refund",
            "reason": "冒烟脚本售后",
            "description": "测试退款链路",
        },
        token=buyer,
    )
    check(bool(sale), "售后申请已提交")

    step("11. 平台处理售后（同意退款 -> 库存回滚）")
    sales = call("GET", "/console/aftersales/?status=pending", token=console)
    target = next((item for item in sales if item["id"] == sale["id"]), None) if sale else None
    check(target is not None, "平台可见待处理售后单")
    if target:
        handled = call(
            "POST",
            "/console/aftersales/",
            {"id": target["id"], "action": "approve", "reply": "冒烟脚本：平台同意退款"},
            token=console,
        )
        check(bool(handled) and handled["status"] == "refunded", "售后已同意退款")
    stock_final = call("GET", f"/products/{pid}/")["stock"]
    check(stock_final == stock_before, f"退款后库存回滚到 {stock_final}")

    step("12. 取消订单回滚库存")
    cancel_data = call("POST", "/orders/", {"sku_id": sku["id"], "quantity": 1}, token=buyer)
    cancel_no = cancel_data["orders"][0]["order_no"] if cancel_data else None
    stock_cancel = call("GET", f"/products/{pid}/")["stock"]
    check(stock_cancel == stock_final - 1, f"立即购买扣减库存：{stock_final} -> {stock_cancel}")
    if cancel_no:
        call("POST", f"/orders/{cancel_no}/cancel/", {"reason": "冒烟脚本取消"}, token=buyer)
        stock_back = call("GET", f"/products/{pid}/")["stock"]
        check(stock_back == stock_final, f"取消订单库存回滚：{stock_cancel} -> {stock_back}")

    step("13. 商家数据隔离与平台跨店查询")
    own = call("GET", "/merchant/orders/?size=5", token=merchant)
    check(own["total"] > 0, f"商家仅见本店 {own['total']} 笔订单")
    cross = call("GET", "/console/orders/?size=5", token=console)
    check(cross["total"] >= own["total"], f"平台可见全站 {cross['total']} 笔订单")
    check(len(cross["results"][0]["shop_names"]) >= 1, "平台订单带店铺信息")
    forbidden = call("GET", "/console/orders/", token=merchant, expect=(403,), allow_error=True)
    check(
        isinstance(forbidden, dict) and forbidden.get("status") == 403,
        "商家访问平台接口被拒绝（403）",
    )

    step("14. 内容运营立即生效")
    banners = call("GET", "/console/banners/", token=console)
    first = banners[0]
    call(
        "PATCH",
        f"/console/banners/{first['id']}/",
        {"subtitle": "冒烟脚本：内容运营已生效"},
        token=console,
    )
    public = call("GET", "/banners/")
    check(
        any(item["id"] == first["id"] and "冒烟脚本" in item["subtitle"] for item in public),
        "平台修改轮播后前台接口立即返回新文案",
    )
    call(
        "PATCH", f"/console/banners/{first['id']}/", {"subtitle": first["subtitle"]}, token=console
    )

    summary()
    return 0 if FAILED == 0 else 1


def summary():
    print("\n" + "=" * 56)
    print(f"  冒烟结果：通过 {PASSED} 项，失败 {FAILED} 项")
    print("=" * 56)
    if FAILED:
        print("  提示：若数据被反复测试污染，可执行")
        print("        backend/.venv/Scripts/python.exe manage.py reset_demo --yes")
    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    sys.exit(main())
