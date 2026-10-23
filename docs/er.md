# ER 图

```mermaid
erDiagram
  USER ||--o{ ADDRESS : owns
  USER ||--o{ ORDER : places
  USER ||--o{ REVIEW : writes
  USER ||--o{ CART_ITEM : owns
  USER ||--o{ AFTER_SALE : requests
  USER ||--o| SHOP : "owner（商家）"
  USER }o--o{ COUPON : claims

  CATEGORY ||--o{ CATEGORY : "parent（三级自关联）"
  CATEGORY ||--o{ SPU : classifies
  BRAND ||--o{ SPU : brands
  SHOP ||--o{ SPU : sells

  SPU ||--o{ SKU : "has（多规格）"
  SPU ||--o{ REVIEW : receives
  SKU ||--o{ CART_ITEM : selected
  SKU ||--o{ ORDER_ITEM : snapshots
  SKU ||--o{ SECKILL_ITEM : targets

  ORDER ||--|{ ORDER_ITEM : contains
  ORDER_ITEM ||--o{ AFTER_SALE : "requests"
  ORDER }o--|| ADDRESS : "address（下单快照）"

  SECKILL_ACTIVITY ||--o{ SECKILL_ITEM : contains
  HOME_FLOOR }o--o| CATEGORY : binds
  HOME_FLOOR ||--o{ BANNER : "同属首页运营位"
```

## 关键字段与约束

| 表 | 关键字段 | 说明 |
| --- | --- | --- |
| `User` | `username`(unique)、`role` | `buyer` / `merchant` / `console` 三角色共用一张表，`username` 即手机号 |
| `Category` | `parent`、`level`、`enabled`、`sort` | 三级自关联，`level ∈ {1,2,3}`；停用后前台隐藏 |
| `Shop` | `owner`、`approved`、`enabled` | 商家账号与店铺一对一；`approved=False` 为待审核 |
| `Spu` | `status`、`image_seed`、`sales`、`review_count` | `status`: draft / pending / on / off / rejected |
| `Sku` | `specs`(JSON)、`price`、`market_price`、`stock` | `specs` 形如 `{"颜色":"曜石黑","版本":"标准版"}` |
| `CartItem` | `(user, sku)` 唯一约束 | 同规格累加数量，受库存上限约束 |
| `Order` | `order_no`(unique)、`batch_no`、`status` | 一次结算按店铺拆单，共用 `batch_no` |
| `OrderItem` | `title_snapshot`、`specs_snapshot`、`price_snapshot` | 快照字段，商品改价不影响历史订单 |
| `AfterSale` | `order_item`、`status`、`amount` | 同意退款时回补库存并置订单 `refunded` |
| `Coupon` | `amount`、`threshold`、`total`、`claimed` | `users` 多对多记录领取关系，防重复领取 |

索引：`Spu(status, category)`、`Order(user, status)`、`Category(parent, enabled)`、`Order.batch_no`。

金额统一 `Decimal(10, 2)`，前端仅做展示格式化，计算全部在后端完成。
