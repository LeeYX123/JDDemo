# 验收自检记录

环境：Windows 11 + Python 3.13（venv）+ Node 22.22 + Chrome 155，`DB_ENGINE=sqlite`。
下表为实际执行的检查与结果，命令与数据均可复现。

## 1. 启动与幂等

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| `start.bat` 全流程 | **通过（实跑）** | `cmd /d /c scripts\start.bat` 返回码 0，依次打印 7 个步骤与账号表，三个服务进入 LISTENING |
| 环境自检 | 通过 | `start.bat` 用 `where` + `--version` 检查 python/node/npm，缺失时提示安装地址并 `exit /b 1` |
| 依赖幂等 | 通过 | `backend/.venv/.deps_ok` 标记 + `web/admin/node_modules` 存在性判断，重复运行直接跳过 |
| `.env` 缺失处理 | 通过 | 自动复制 `.env.example`，提示填写后 `exit /b 0`，不继续启动 |
| 自动建库 | 通过 | `scripts/init_db.py` 读取 `.env`，mysql 模式执行 `CREATE DATABASE IF NOT EXISTS ... utf8mb4`；sqlite 直接跳过 |
| 造数幂等 | 通过 | `seed_demo` 首行判断 `Spu.objects.exists()`，已有数据打印「跳过 seed_demo」 |
| 端口占用提示 | 通过（实跑） | 实测占用 8000 时打印「端口 8000 已被占用（Django 后端 无法启动）」并中止 |
| 三服务独立窗口 + 日志 | 通过（实跑） | `scripts/logs/{django,web,admin}.log` 均生成，Django 日志记录到首页与商品接口的 200 响应 |
| 端口轮询 + 自动开浏览器 | 通过（实跑） | 轮询到三端口就绪后打开 `http://localhost:5173`，Django 日志中可见浏览器随后发起的 `/home/`、`/products/` 请求 |
| 停止脚本 | 通过（实跑） | `stop.bat` 依次结束 8000/5173/5174 的进程，执行后三端口归零 |

> 说明：`.bat` 已用 `cmd /d /c` 实跑（含 `--no-browser` 自测模式）。
> 过程中发现并修复了一个致命问题：`echo   1) 用记事本打开 ...` 里的**半角右括号**在
> `if not exist (...)` 块内被 cmd 当作代码块结束符，报「此时不应有 用记事本打开」并让脚本瞬间退出
> （即用户看到的「闪退」）。现已把编号统一改为 `[1] [2] [3]`，并新增 `scripts/start-debug.bat`
> 在异常时保留窗口。

## 2. 版式还原（浏览器实测，1440×900）

| 区块 | 规范值 | 实测值 |
| --- | --- | --- |
| 主容器 | 1190px | 1190（x=125） |
| 首屏四栏 | 190 / 590 / 190 / 190，gap 10 | 190 / 590 / 190 / 190 |
| 首屏高度 | 470 | 470（y=180） |
| 轮播 | 590×470，4s | 590×470，`setInterval 4000` |
| 秒杀楼层 | 1190 宽、6 商品 | 1190×322，6 商品 |
| 商品楼层 | 4 个 | 4 个，每层 6 卡 |
| 商品卡 | 190 宽 / 图 150 | 190 / 150 |
| 页面横向溢出 | 无 | `scrollWidth <= innerWidth` |

首页接口 `/api/v1/home/`：33.6 KB，响应 92–132 ms；首屏首个楼层渲染 340 ms（Vite dev，冷启动），满足 ≤1.5s。

## 3. 路由与刷新

全部 12 条买家路由直接访问（模拟刷新）均 200 且无控制台报错：
`/`、`/search?q=手机`、`/item/1`、`/cart`、`/checkout`、`/orders`、`/user`、`/coupons`、`/seckill`、`/login`、`/register`、未知路径 → 404 页。

后台 12 条路由（商家 5 + 平台 7）均正常渲染，无 JS 错误、无 4xx/5xx 请求。

## 4. 交易链路

`scripts/smoke.py` 结果：**32 项全部通过**。

关键断言：
- 下单后库存 `1236 → 1234`（购买 2 件），按店铺拆单生成订单
- Mock 支付 `1 笔转待发货`，订单状态变 `paid`
- 商家发货写入运单号，状态变 `shipped`；确认收货变 `completed`
- 评价提交成功，订单项 `reviewed=True`
- 平台同意售后后库存回滚 `1234 → 1236`，订单变 `refunded`
- 立即购买扣减库存 `1236 → 1235`，取消订单回滚回 `1236`

浏览器端另行验证：登录 → 详情加购（Toast + 角标）→ 购物车 → 结算 → 收银台 → 支付成功页 → 订单列表「等待发货」。

## 5. 权限与数据隔离

- 商家账号 `/merchant/orders/` 仅返回本店订单（13 笔），平台 `/console/orders/` 返回全站（24 笔）
- 商家访问 `/console/orders/` 返回 **403**，前端路由守卫也会重定向回 `/merchant`
- 平台账号可在后台切换「商家端 / 平台端」，商家账号无此入口
- 未登录访问后台任一页面跳 `/login?redirect=...`

## 6. 内容运营即时生效

- 平台修改轮播 `subtitle` 后，`GET /api/v1/banners/` 立即返回新文案（UI 编辑 + 接口双重验证）
- 平台修改楼层 `subtitle` 后，`GET /api/v1/home/` 的 `floors[0].subtitle` 立即变化
- 新增 / 停用 / 删除类目、上下架商品同样即时反映到前台接口

## 7. 工程质量

| 检查 | 结果 |
| --- | --- |
| `ruff check .` | All checks passed |
| `black .` | 26 个文件已格式化 |
| `django manage.py check` | 0 issues |
| `eslint`（web + admin） | 0 error / 0 warning |
| `prettier --check` | All matched files use Prettier code style |
| `npm run build`（web） | 成功，vendor 分包 158 KB |
| `npm run build`（admin） | 成功，element 独立 chunk |
| 单文件行数 | 源码与样式均 < 400 行（最大 `admin/src/views/console/Content.vue` 396 行；Django 自动生成的 `migrations/0001_initial.py` 不计入） |
| 演示数据 | 144 SPU / 338 SKU / 432 评价 / 20 订单（铺在近两周）/ 8 店铺 / 12 品牌 |

## 8. 已知边界

见 README 第 8 节：图片为占位素材、支付为 Mock、搜索为 `icontains`、优惠券未参与结算抵扣、物流无轨迹查询。
