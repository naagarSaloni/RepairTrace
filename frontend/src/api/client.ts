import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL || undefined,
  timeout: 15000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('repairtrace_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('repairtrace_token')
      localStorage.removeItem('repairtrace_session')
      window.dispatchEvent(new Event('repairtrace:logout'))
    }

    return Promise.reject(error)
  }
)

export const assetUrl = (path?: string | null) => {
  if (!path) return ''

  if (/^https?:\/\//i.test(path)) return path

  return `${API_URL}${path.startsWith('/') ? '' : '/'}${path}`
}

export const errorMessage = (error: any) => {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    return detail.map((x: any) => x.msg).join(', ')
  }

  return error?.message || 'Something went wrong. Please try again.'
}