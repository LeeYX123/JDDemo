import axios from 'axios'

const request = axios.create({ baseURL: '/api/v1', timeout: 15000 })

let notify = () => {}
export function setNotify(fn) {
  notify = fn
}

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('jd_access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use(
  (res) => {
    const body = res.data
    if (!body || typeof body.code === 'undefined') return body
    if (body.code !== 0) {
      const error = new Error(body.msg || '请求失败')
      error.code = body.code
      notify(body.msg || '请求失败')
      return Promise.reject(error)
    }
    return body.data
  },
  (err) => {
    const status = err.response?.status
    const msg =
      err.response?.data?.msg ||
      (status === 401 ? '请先登录' : status ? `请求失败（${status}）` : '网络异常，请稍后重试')
    if (status === 401) {
      localStorage.removeItem('jd_access')
      localStorage.removeItem('jd_refresh')
      localStorage.removeItem('jd_user')
      const next = location.pathname + location.search
      if (!location.pathname.startsWith('/login')) {
        location.href = `/login?next=${encodeURIComponent(next)}`
      }
    } else {
      notify(msg)
    }
    return Promise.reject(err)
  }
)

export const api = {
  get: (url, params) => request.get(url, { params }),
  post: (url, data) => request.post(url, data),
  patch: (url, data) => request.patch(url, data),
  delete: (url) => request.delete(url),
}
