# 任务
一比一复刻 https://www.jd.com/ 的整站前端版式与交互，前端 Vue 3 单页应用，后端 Python + Django REST Framework，数据库 MySQL，并配套商家管理后台与平台管理后台。
要求不是"风格类似"，而是逐屏对照、像素级对齐。评图方式：把自己实现的页面截图与参照站同屏叠加比对，模块位置、尺寸、字号、颜色偏差不得肉眼可见。

# 技术栈（固定）
前端（买家端）：Vue 3.4 + Vite 5 + Vue Router 4 + Pinia + Axios + 原生 CSS（不引 UI 组件库，避免组件默认样式破坏还原度）
前端（后台端）：Vue 3 + Vite + Element Plus + Pinia（商家后台与平台后台共用一个 SPA，按角色渲染菜单与路由守卫）
后端：Python 3.12 + Django 5.x + Django REST Framework + SimpleJWT + MySQL 8.0(utf8mb4) + django-cors-headers
目录：monorepo —— backend/  web/  admin/  scripts/  docs/
前后端联调：开发态不引入 nginx，用 Vite dev server 的 proxy 把 /api 转发到 Django:8000

# 视觉规范（照抄，不要自行优化）
主色 #e1251b，按压/深色 #c81623，链接 hover 同主色
页面底色 #f4f4f4，正文 #333，次要 #666，辅助 #999，分割线 #eee / #e8e8e8
主容器 1190px 居中；字体 "Microsoft YaHei", "PingFang SC", sans-serif
字号层级 12 / 13 / 14 / 16 / 18 / 20 / 24px；金额数字加粗
圆角：按钮 2px，卡片 4px，图片 4px
顶部工具条 30px 高 #e3e4e5，12px 字，右侧链接 1px 竖线分隔
头部 100px 高白底；搜索框 550×36，2px 主色边框；搜索按钮主色实底；下方 12px 热搜词一行
主导航 40px 高；左侧"全部商品分类"主色块 190px 宽
首屏三栏 190 + 590 + 190，轮播 590×470，自动播放 4s，圆点 + 左右箭头 + 圆角
商品卡宽 190，主图 150×150，标题两行截断 12px，价格 18px 主色，"已售/评价" 12px 灰
楼层标题条 36px 高，标题 20px 加粗 + 右侧 Tab + 更多箭头
页脚：服务保障四宫格 + 五列链接 + 备案占位
交互：可点元素 hover 必须有反馈；加购飞入动画或 Toast；轮播、Tab、横滑、筛选联动全部实现

# 素材占位（保持尺寸位置一致，交付后可直接替换）
Logo 用自建 wordmark（红色圆角块 + 白色字形）；商品图用统一封装组件 ProductImage（emoji + 8 套渐变底色，按 id 取色）；
图标用内联 SVG；文案用原创中文商品名。版式、间距、字号、颜色、动画一律对齐参照站，不因占位改动尺寸。

# 买家端页面（Vue Router 路由一一对应）
/                首页：顶部工具条 → 头部搜索 → 主导航 → 首屏三栏（三级类目悬停浮层 / 轮播 / 快报+服务九宫格）
                 → 秒杀楼层（倒计时+进度条+6 商品）→ 商品楼层 ×4（Tab + 横滑箭头）→ 猜你喜欢（滚动到底加载）
/search          搜索列表：筛选栏（类目/品牌/价格区间）+ 排序栏 + 网格 + 分页 + 已选条件回显
/item/:id        商品详情：面包屑 + 主图/缩略图/放大镜 + 价格块 + 促销标签 + SKU 联动画价联库 + 数量 + 加购/立即购买 + 店铺卡 + 详情与评价 Tab
/cart            购物车：全选 + 按店铺分组 + 数量增减 + 失效区 + 吸底结算栏
/checkout        订单确认：地址选择与新增 + 按店铺拆单 + 运费规则（满 99 免运费）+ 备注 + 提交
/pay/:orderNo    收银台（Mock 支付）+ 支付结果页
/orders          我的订单：状态 Tab + 差异化操作按钮（付款/取消/确认收货/评价/申请售后）
/orders/:orderNo 订单详情：进度条 + 商品清单 + 金额明细 + 物流 + 售后记录
/user            个人中心：资料 / 地址管理 / 我的评价 / 优惠券
/login /register 登录注册，验证码固定 8888，登录后按 next 跳回
/coupons /seckill 领券中心、秒杀会场（时间允许再做）

# 后台端（一个 admin SPA，路由守卫按角色分流）
/merchant：深色侧栏 + 内容区 —— 数据看板（今日订单/GMV/待发货/待售后/在售数 + 近 7 日柱图，纯 SVG 即可）
           商品管理（列表/搜索/上下架/新增编辑）、订单管理（状态 Tab + 一键发货填运单号）、
           售后管理（同意/驳回，同意后回滚库存）、店铺设置
/console： 蓝色系区分 —— 数据看板（GMV/订单/买家/店铺/待办/趋势/店铺排行/类目分布）、
           类目管理（三级树+新增+启停+删除保护）、商家审核、商品审核（通过/驳回/强制下架）、
           订单中心（跨店查询）、内容运营（轮播/楼层/快报，改完前台立即生效）、用户管理

# 接口层要求
用 DRF ViewSet 或 APIView 统一风格，路径统一 /api/v1/ 前缀：
/api/v1/auth/（登录、注册、刷新 token、当前用户）
/api/v1/categories/  /api/v1/banners/  /api/v1/floors/  /api/v1/products/（列表/详情/筛选排序分页/搜索）
/api/v1/cart/（增删改查、勾选、全选）  /api/v1/orders/（提交、列表、详情、取消、确认收货）
/api/v1/payment/（Mock 支付回调）  /api/v1/reviews/  /api/v1/aftersales/  /api/v1/coupons/
/api/v1/merchant/（看板、商品、订单发货、售后）
/api/v1/console/（看板、类目、商家、商品审核、订单、内容、用户）
统一响应结构 {code, msg, data}；统一分页 {page, size, total, results}；统一异常处理与错误码。
前端封装 request.js：注入 JWT、401 自动跳登录、错误统一提示、loading 状态。
CORS 白名单放行 5173 / 5174；Vite proxy 配置 /api → http://127.0.0.1:8000。

# 数据模型
User、Address、Category(三级自关联)、Brand、Shop、Spu、Sku、CartItem、Order、OrderItem(标题与价格快照)、
Review、AfterSale、Banner、Notice、HomeFloor、SeckillActivity、SeckillItem、Coupon。
金额统一 Decimal(10,2)；下单在事务内 select_for_update 扣库存；按店铺拆单；订单状态集中枚举管理。

# 演示数据（必须有内容，不能出现空列表）
seed_demo 一键生成：8 个一级类目 / 每类 3 个二级 / 每二级 2 个三级；
≥140 个 SPU、≥300 个 SKU，原创中文标题（例："星野 旗舰 5G 智能手机 12GB+256GB 曜石黑"）；
12 个虚构品牌、8 家店铺；价格分布贴近真实（3C 千元级、服饰百元级、生鲜几十元级，带划线价）；
每个商品带销量、评价数与 ≥3 条评价正文；预置 20 笔历史订单覆盖五种状态；
三个账号在登录页做一键填充：买家 13800138000/123456、商家 13900139000/123456、平台 13700137000/123456。
另提供 reset_demo 一键恢复初始数据。

# 启动方式（不要 Docker，不用 nginx，一个脚本跑完）
交付 scripts/start.bat（Windows）与 scripts/start.sh（macOS/Linux），以及 scripts/stop.bat 关闭全部服务。
start.bat 要求全自动完成以下步骤，任何一步失败都要停下来把原因打印清楚，不要静默跳过：
1. 环境自检：python / node / npm / mysql 版本，缺哪个直接提示去哪装，并退出
2. 首次运行：创建 backend/.venv → pip install -r requirements.txt → 前端 web/ 与 admin/ 分别 npm install（已装则跳过）
3. 检查 backend/.env 是否存在，不存在则从 .env.example 复制并提示"请先填写数据库密码后重新运行"，然后退出
4. 自动建库：读取 .env 里的连接信息，执行 CREATE DATABASE IF NOT EXISTS jdshop DEFAULT CHARACTER SET utf8mb4
5. python manage.py migrate → python manage.py seed_demo（已存在数据则跳过）
6. 依次启动三个服务，各开独立窗口并写日志到 scripts/logs/：
   Django 127.0.0.1:8000、买家端 5173、后台端 5174
7. 等待端口就绪（轮询检测，最多 30 秒），然后自动打开浏览器到 http://localhost:5173
8. 控制台打印演示账号表与各入口地址
其他要求：
- 脚本要能重复执行，第二次运行不再重复装依赖、不重复造数
- .bat 文件用 GBK 编码保存并配合默认代码页，不要写 chcp 65001，避免中文乱码与吞行
- 端口被占用时给出明确提示，而不是启动失败后一片空白
- 允许 .env 中 DB_ENGINE=sqlite 作为无 MySQL 机器的演示兜底，此时跳过建库步骤

# 性能与工程
首页首屏 ≤ 1.5s；列表接口 N+1 全消除；商品图懒加载；
Vite 分包（vendor / element-plus 单独 chunk）。
代码风格：ESLint + Prettier（前端）、ruff + black（后端）；组件按功能分目录，禁止单文件超 400 行。

# 交付物
完整可运行代码（backend / web / admin / scripts 四目录）、requirements.txt、package.json、.env.example；
README（双击 start.bat 即可、三个账号、各入口地址、常见启动问题排查）；
docs/：ER 图（mermaid）、接口清单、订单状态机、目录结构说明；
冒烟脚本跑通：登录→搜索→详情选规格→加购→结算→支付→商家发货→确认收货→评价→售后→平台处理。

# 验收（自检后逐条回报）
[ ] 双击 start.bat，从零到浏览器打开首页全程无人值守，中途只需填写一次数据库密码
[ ] 首页截图与参照站逐区块比对，模块顺序 / 栅格 / 字号 / 颜色一致
[ ] 全部路由可访问，且刷新页面不 404（Vite dev server 需开启 historyApiFallback）
[ ] 下单链路一次跑通，库存正确扣减，取消订单库存回滚
[ ] 商家数据隔离，平台可跨店查询
[ ] 平台后台改轮播/楼层后前台刷新立即生效
[ ] 第二次运行 start.bat 不重复装依赖、不重复造数，10 秒内启动完成

# 执行顺序
1. 先出页面清单 + ER 图 + 目录结构 + 接口清单 + 视觉规范表，我确认后再写代码
2. 依次交付：模型与 seed → 接口 → 买家端首页 → 详情与购物车 → 下单支付 → 订单售后 → 商家后台 → 平台后台 → 启动脚本与文档
3. 信息不足时一次性列出不超过 5 个问题，不要臆造规则
4. 未实现或降级处必须标 TODO 及原因，禁止假页面冒充完成
