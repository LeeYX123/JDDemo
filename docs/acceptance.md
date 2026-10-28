# 验收自检记录

环境：Windows 11 + Python 3.13（venv）+ Node 22.22 + Chrome 155，`DB_ENGINE=sqlite`。
下表为实际执行的检查与结果，命令与数据均可复现。

## 1. 启动与自举

### 1.1 零环境自举（模拟“什么都没装”的电脑）

测试方法：把 `PATH` 裁剪为只剩 `C:\Windows\System32;C:\Windows`（不含 Python / Node），再执行启动脚本。

| 检查项 | 结果 | 实测证据 |
| --- | --- | --- |
| Node 自动下载解压 | **通过** | 下载 `node-v22.14.0-win-x64.zip` 并解压到 `.runtime\node-v22.14.0`，`node -v` = v22.14.0、`npm -v` = 10.9.2 |
| Python 自动下载安装 | **通过** | 从华为云镜像下载 `python-3.12.8-amd64.exe`，静默安装到 `.runtime\python-3.12.8`，`python -V` = 3.12.8、pip 24.3.1 |
| 无需管理员权限 | 通过 | 安装参数 `InstallAllUsers=0 TargetDir=<项目>\.runtime\...`，全程未提权 |
| 环境变量落盘 | 通过 | 生成 `scripts/logs/env.cmd`，内容为 `SYS_PY`、`JD_NODE_DIR`、`PATH` 前置 |
| 便携 Python 建虚拟环境 | **通过** | 用 `.runtime\python-3.12.8\python.exe` 创建独立 venv，成功安装 Django 5.2.18 等依赖 |
| 下载失败兜底 | 通过 | 每个地址都尝试“代理 → 直连”，并用 curl + .NET 两套下载实现；实测代理失效时自动直连成功 |
| 整体耗时 | 25 秒 | Node 复用缓存 + Python 下载安装（不含依赖安装） |

### 1.2 已有环境（含版本过低 / 环境损坏）

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 版本探测 | 通过 | 依次扫描 PATH、`Program Files\nodejs`、`%APPDATA%\nvm`、`%LOCALAPPDATA%\Programs\Python*` 等常见位置，取满足 3.10+ / 18+ 的最高版本 |
| 版本过低 | 通过（逻辑验证） | 低版本会被记录为 `any`，随后改用 `.runtime` 便携版，不改动系统环境 |
| 虚拟环境损坏 | 通过（代码路径） | 无法执行或版本过低时删除重建 |
| 依赖增量 | **通过（实跑）** | `requirements.txt` 与 `package-lock.json` 的 md5 与标记比对，二次启动输出「依赖无变化，跳过」 |
| 端口残留 | **通过（实跑）** | 上一轮残留的 `python.exe` / `node.exe` 被自动结束；非本项目进程则明确拒绝 |
| 演示数据过期 | **通过（实跑）** | `refresh_demo` 把过期的秒杀场次顺延到当前窗口，冒烟恢复 32/32 |
| 幂等 | **通过（实跑）** | 第二次启动全程跳过环境、依赖、造数，直接进入服务启动 |

> 说明：`.bat` 全程用 `cmd /d /c` 实跑验证（含 `--no-browser` 自测模式）。
> 过程中修复的问题：
> 1. `echo 1) ...` 的半角右括号在 `if (...)` 块内被当成代码块结束符 → 脚本秒退（已改为 `[1]`）；
> 2. 环境里同时存在 `http_proxy` 与 `HTTP_PROXY` 时，`Get-ChildItem Env:` 与 `Start-Process` 会报
>    “字典中的关键字重复” → 增加兼容模式，下载改用进程内实现；
> 3. `tasklist` CSV 取错列导致把 PID 当进程名 → 改为取第 1 列，并处理“PID 已退出”的残留端口。

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
