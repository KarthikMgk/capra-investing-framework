import axios from "axios"

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "",
  withCredentials: true,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const url: string = error.config?.url ?? ""
    const isAuthEndpoint =
      url.includes("/auth/login") || url.includes("/auth/me")
    if (error.response?.status === 401 && !isAuthEndpoint) {
      window.location.href = "/login"
    }
    return Promise.reject(error)
  },
)

export default apiClient
