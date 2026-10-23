# JD Demo · 京东版式还原演示

按 `prompt.md` 要求实现的京东（jd.com）整站前端版式与交互复刻，含**买家端商城**、**商家后台**、**平台后台**三套界面与完整交易链路。前端 Vue 3 + Vite，后端 Django REST Framework，数据库默认 SQLite（可切 MySQL 8）。

> 本项目仅用于前端版式与交互还原的技术演示，与京东官方无关；所有商品、品牌、店铺、评价均为虚构数据，图片位置使用 `ProductImage` 占位组件，交付后可直接替换为真实素材。

## 效果速览

| 买家端首页 | 商品详情 |
| ----- | ---- |
| 买家端首页 | 商品详情 |

| 商家后台看板 | 平台后台看板 |
| ------ | ------ |
| 商家看板   | 平台看板   |

截图来自本地实跑（1440×900，Chrome 无头），详见 `docs/screenshots/`。

---

## 1. 一键启动

### Windows

双击 **`scripts/start.bat`**。首次运行会自动完成：

1. 环境自检（python / node / npm，缺失时给出安装提示并中止）
2. 创建 `backend/.venv` 并安装 `requirements.txt`；`web/` 与 `admin/` 分别 `npm install`（已安装则跳过）
3. 检查 `backend/.env`，不存在则从 `.env.example` 复制并提示填写后重新运行
4. 按 `.env` 创建 MySQL 数据库（`DB_ENGINE=sqlite` 时自动跳过）
5. `migrate` + `seed_demo`（已有数据则跳过造数）
6. 开三个独立窗口启动 Django(8000) / 买家端(5173) / 后台端(5174)，日志写入 `scripts/logs/`
7. 轮询等待三个端口就绪（最长 30 秒）后自动打开浏览器

再次运行是幂等的：不会重复装依赖、不会重复造数，通常 10 秒内完成。

停止服务：双击 **`scripts/stop.bat`**。

> 排查用：`scripts/start-debug.bat` 会在脚本结束后保留窗口并打印完整输出；
> 无界面环境（CI / 远程）可用 `scripts\start.bat --no-browser` 跳过自动打开浏览器。

### macOS / Linux

```bash
bash scripts/start.sh     # 启动
bash scripts/stop.sh      # 停止
```

### 使用 MySQL（可选）

编辑 `backend/.env`：

```ini
DB_ENGINE=mysql
DB_NAME=jdshop
DB_USER=root
DB_PASSWORD=你的密码
DB_HOST=127.0.0.1
DB_PORT=3306
```

再运行 start 脚本，会自动 `CREATE DATABASE IF NOT EXISTS jdshop DEFAULT CHARACTER SET utf8mb4`。  
没有 MySQL 时保持 `DB_ENGINE=sqlite` 即可开箱演示。

---

## 2. 演示账号与入口

| 角色 | 手机号         | 密码     | 入口                               |
| -- | ----------- | ------ | -------------------------------- |
| 买家 | 13800138000 | 123456 | <http://localhost:5173>          |
| 商家 | 13900139000 | 123456 | <http://localhost:5174/merchant> |
| 平台 | 13700137000 | 123456 | <http://localhost:5174/console>  |



| 服务                    | 地址                              |
| --------------------- | ------------------------------- |
| 买家端商城                 | <http://localhost:5173>         |
| 运营后台（商家 + 平台共用一个 SPA） | <http://localhost:5174>         |
| REST API              | <http://127.0.0.1:8000/api/v1/> |

登录页均提供「演示账号一键填充」；买家端登录后按 `next` 参数跳回原页面。

---

## 3. 功能概览

**买家端**（`web/`，Vue Router 路由与页面一一对应）

- `/` 首页：顶部工具条 → 头部搜索 → 主导航 → 首屏四栏（190 三级类目浮层 / 590×470 轮播 / 快报九宫格 / 秒杀栏）→ 秒杀楼层（倒计时 + 进度条 + 6 商品）→ 商品楼层 ×4（Tab + 横滑）→ 猜你喜欢（滚动加载）
- `/search` 搜索：类目 / 品牌 / 价格区间 / 仅看有货筛选 + 综合·销量·价格·新品排序 + 已选条件回显 + 分页
- `/item/:id` 详情：面包屑、主图与缩略图、价格块与促销标签、SKU 联动、数量、加购 / 立即购买、店铺卡、详情与评价 Tab
- `/cart` 购物车：全选、按店铺分组、数量增减、失效区、吸底结算栏
- `/checkout` 结算：地址选择与新增、按店铺拆单、满 99 免运费、备注
- `/pay/:batchNo` 收银台：Mock 支付 + 支付结果页（三步进度）
- `/orders`、`/orders/:orderNo`：状态 Tab、差异化操作（付款 / 取消 / 确认收货 / 评价 / 售后）、进度条与物流
- `/user` 个人中心：资料 / 地址管理 / 我的评价 / 优惠券
- `/coupons`、`/seckill`：领券中心、秒杀会场
- `/login`、`/register`：验证码固定 8888，登录后回跳

**商家后台**（`admin/`，深色侧栏 + 京东红）

- 数据看板：今日订单 / 今日 GMV / 待发货 / 待售后 / 在售商品 + 近 7 日柱图 + 热销 Top5 + 最近订单
- 商品管理：列表 / 搜索 / 状态筛选 / 上下架 / 新增与编辑（三级类目 + 品牌 + 价格库存）
- 订单管理：状态 Tab + 一键发货（填物流公司与运单号）+ 订单详情抽屉
- 售后管理：同意（自动回滚库存）/ 驳回（订单回到已完成）
- 店铺设置：店铺名称、简介、Logo 标识

**平台后台**（`admin/`，深蓝侧栏 + 蓝色强调）

- 数据看板：平台 GMV / 今日 GMV / 订单总量 / 买家数 / 入驻店铺 / 待办审核 + 折线趋势 + 店铺排行 + 类目分布
- 类目管理：三级树、新增子类目、启停、删除（子类目与商品保护）
- 商家审核：通过 / 驳回 / 停用 / 恢复
- 商品审核：通过 / 驳回（填原因）/ 强制下架 / 恢复上架
- 订单中心：跨店查询 + 平台售后工单处理
- 内容运营：轮播 / 楼层 / 快报 CRUD，保存后前台刷新立即生效
- 用户管理：按角色查询、禁用 / 启用（平台账号受保护）

---

## 4. 目录结构

```text
JD_Demo/
├─ backend/                 Django 5 + DRF
│  ├─ jdshop/               settings / urls / wsgi
│  └─ store/
│     ├─ models.py          17 张业务表（金额 Decimal(10,2)）
│     ├─ serializers.py     序列化与快照字段
│     ├─ views/             auth / catalog / cart / orders / merchant / console
│     ├─ permissions.py     IsMerchant / IsConsole
│     ├─ responses.py       统一 {code,msg,data} 与异常处理
│     ├─ utils.py           订单号生成、统一分页
│     └─ management/commands/  seed_demo.py、reset_demo.py
├─ web/                     买家端 Vue 3 SPA
│  └─ src/{components,pages,styles,stores.js,router.js,api.js}
├─ admin/                   运营后台 Vue 3 + Element Plus SPA
│  └─ src/{layouts,views/merchant,views/console,components,store,styles}
├─ scripts/                 start/stop 脚本、init_db.py、smoke.py、logs/
├─ docs/                    接口清单、ER 图、状态机、目录结构、视觉规范
├─ requirements.txt
├─ package.json             根级 lint / format / build 脚本
└─ pyproject.toml           ruff + black 配置
```

详细说明见 `docs/structure.md`。

---

## 5. 接口约定

- 统一前缀 `/api/v1/`，统一响应 `{code, msg, data}`，`code=0` 表示成功
- 分页响应 `{page, size, total, results}`，参数 `page` / `size`
- 认证：SimpleJWT，`Authorization: Bearer <access>`；401 时前端自动清理 token 并跳登录
- CORS 白名单：`http://localhost:5173`、`http://localhost:5174` 及 127.0.0.1 等价来源
- 开发态不引入 nginx，Vite 将 `/api` 代理到 `http://127.0.0.1:8000`

完整接口表见 `docs/api.md`。

---

## 6. 数据与自检脚本

```bash
# 生成演示数据（幂等：已有数据则跳过）
backend/.venv/Scripts/python.exe manage.py seed_demo

# 清库并重建演示数据（恢复初始状态）
backend/.venv/Scripts/python.exe manage.py reset_demo --yes

# 端到端冒烟：登录→搜索→详情→加购→结算→支付→发货→收货→评价→售后→平台处理
backend/.venv/Scripts/python.exe scripts/smoke.py
```

演示数据规模：8 个一级类目 / 24 个二级 / 48 个三级、144 个 SPU、338 个 SKU、12 个品牌、8 家店铺、432 条评价、20 笔历史订单（铺在近两周，覆盖 5 种状态）。

> 冒烟脚本会真实创建订单与售后单。如果希望恢复到干净的初始演示数据，执行一次 `reset_demo --yes`。

### 代码风格

```bash
npx eslint "web/src/**/*.{js,vue}" "admin/src/**/*.{js,vue}"   # 前端 lint
npx prettier --check "web/src/**/*.{js,vue}" "admin/src/**/*.{js,vue}"
cd backend && .venv/Scripts/ruff.exe check . && .venv/Scripts/black.exe --check .
```

---

## 7. 常见问题排查

| 现象                  | 原因与处理                                                                    |
| ------------------- | ------------------------------------------------------------------------ |
| 双击 `start.bat` 窗口一闪而过 | 已修复：`echo 1) ...` 里的半角右括号会被 cmd 当成代码块结束符。若再遇到，改用 `scripts/start-debug.bat`，它结束后保留窗口并显示完整报错 |
| 提示端口被占用             | 先运行 `scripts/stop.bat`；仍被占用则用 `netstat -ano \| findstr :8000` 找到 PID 后结束 |
| `npm install` 很慢或失败 | 切换 npm 镜像 `npm config set registry https://registry.npmmirror.com` 后重试   |
| pip 安装失败            | 使用国内源 `-i https://pypi.tuna.tsinghua.edu.cn/simple`，或检查代理设置              |
| 页面打开是白屏             | 打开 `scripts/logs/web.log` 看 Vite 报错；确认 `web/node_modules` 已安装完成          |
| 后台登录提示「不是商家或平台账号」   | 商家/平台账号只能在 5174 登录，买家账号请走 5173                                           |
| MySQL 连接失败          | 检查 `backend/.env` 的 `DB_USER` / `DB_PASSWORD`，确认 MySQL 服务已启动且端口一致        |
| 刷新页面 404            | 确认使用 start 脚本启动的 Vite 开发服务器（已开启 SPA history fallback）                    |
| 图表/看板数字为 0          | 数据被清空或时间跨天，执行 `reset_demo --yes` 重新造数                                    |

日志位置：`scripts/logs/django.log`、`web.log`、`admin.log`。

---

## 8. 已知边界（如实标注）

- **图片素材**：商品图、Logo、图标全部为占位实现（emoji + 8 套渐变 / 自建 wordmark / 内联 SVG），尺寸与位置按参照站固定，替换真实图片不会引起版式位移。
- **支付**：`/api/v1/payment/mock/` 为 Mock 支付，不接入真实支付渠道。
- **搜索**：使用 `icontains` 模糊匹配（标题 / 副标题 / 标签 / 品牌 / 三级类目名），未接入分词与搜索引擎。
- **优惠券**：支持领取与个人中心展示，结算页未实现券抵扣计算。
- **物流**：运单号仅存储展示，未接入物流轨迹查询。
- **性能**：首页接口已做 `select_related` / `prefetch_related` 消除 N+1，商品图懒加载与 Vite 分包已配置；未做 CDN 与图片压缩。
