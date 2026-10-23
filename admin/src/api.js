import axios from 'axios'
import { ElMessage } from 'element-plus'

/** 后台统一请求：注入 JWT、解包 {code,msg,data}、401 回登录页。 */
const request = axios.create({ baseURL: '/api/v1', timeout: 15000 })

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('jd_admin_access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use(
  (res) => {
    const body = res.data
    if (!body || typeof body.code === 'undefined') return body
    if (body.code !== 0) {
      ElMessage.error(body.msg || '请求失败')
      return Promise.reject(new Error(body.msg || '请求失败'))
    }
    return body.data
  },
  (err) => {
    const status = err.response?.status
    const msg =
      err.response?.data?.msg ||
      (status === 403
        ? '没有权限访问该资源'
        : status
          ? `请求失败（${status}）`
          : '网络异常，请检查后端服务是否已启动')
    if (status === 401) {
      localStorage.removeItem('jd_admin_access')
      localStorage.removeItem('jd_admin_user')
      if (!location.pathname.startsWith('/login')) {
        location.href = `/login?redirect=${encodeURIComponent(location.pathname)}`
      }
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  }
)

export const api = {
  get: (url, params) => request.get(url, { params }),
  post: (url, data) => request.post(url, data),
  patch: (url, data) => request.patch(url, data),
  del: (url) => request.delete(url),
}
