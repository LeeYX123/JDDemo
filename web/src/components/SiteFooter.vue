<script setup>
import Icon from './Icon.vue'

const SERVICES = [
  { icon: 'shield', title: '正品保障', desc: '正品行货 放心购买' },
  { icon: 'truck', title: '极速配送', desc: '京东物流 次日送达' },
  { icon: 'refresh', title: '无忧售后', desc: '7 天无理由退换货' },
  { icon: 'service', title: '贴心服务', desc: '7×24 小时客服在线' },
]
const COLUMNS = [
  { title: '购物指南', links: ['购物流程', '会员介绍', '生活旅行', '常见问题', '大家电'] },
  { title: '配送方式', links: ['上门自提', '211 限时达', '配送服务查询', '配送费收取标准', '海外配送'] },
  { title: '支付方式', links: ['货到付款', '在线支付', '分期付款', '公司转账', '京东白条'] },
  { title: '售后服务', links: ['售后政策', '价格保护', '退款说明', '返修/退换货', '取消订单'] },
  { title: '商家服务', links: ['商家入驻', '商家后台', '平台规则', '营销中心', '服务市场'] },
]
</script>

<template>
  <footer class="footer">
    <div class="footer-service">
      <div class="wrap footer-service-in">
        <div v-for="item in SERVICES" :key="item.title" class="service-cell">
          <span class="ico"><Icon :name="item.icon" :size="22" /></span>
          <div>
            <b>{{ item.title }}</b
            ><span>{{ item.desc }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="wrap footer-links">
      <div v-for="col in COLUMNS" :key="col.title" class="footer-col">
        <h4>{{ col.title }}</h4>
        <a v-for="link in col.links" :key="link">{{ link }}</a>
      </div>
      <div class="footer-col footer-contact">
        <h4>京东客服</h4>
        <p class="phone">400-606-5500</p>
        <p>服务时间 9:00 - 22:00</p>
        <RouterLink to="/user" class="btn btn-ghost btn-sm">个人中心</RouterLink>
      </div>
    </div>

    <div class="footer-copy">
      <p>
        关于我们<span class="sep">|</span>联系我们<span class="sep">|</span>商家入驻<span class="sep">|</span
        >营销中心<span class="sep">|</span>友情链接
      </p>
      <p>© 2004 - 2026 京东JD.com 版权所有 · 本项目为前端还原演示，非真实商城</p>
      <p>
        京ICP备00000000号<span class="sep">|</span>京公网安备 00000000000000 号<span class="sep">|</span
        >增值电信业务经营许可证
      </p>
    </div>
  </footer>
</template>
