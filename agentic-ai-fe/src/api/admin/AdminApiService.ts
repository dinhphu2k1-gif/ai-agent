import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

import type { ApiResponse } from '@/api/index'

import { AdminApiError } from './errors'
import { unwrapEnvelope } from './unwrap'

type AdminErrorPayload = {
  code?: string
  field?: string | null
}

const ADMIN_BASE_PATH = '/api/v1/admin'

export class AdminApiService {
  protected axiosInstance: AxiosInstance

  constructor() {
    const rootUrl = import.meta.env.VITE_APP_API_URL ?? ''
    this.axiosInstance = axios.create({
      baseURL: `${rootUrl}${ADMIN_BASE_PATH}`,
      timeout: 60000,
    })
    this.axiosInstance.interceptors.request.use(this.applyAdminHeaders)
  }

  private applyAdminHeaders(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
    if (!config.headers) {
      config.headers = {}
    }

    const adminToken = import.meta.env.VITE_ADMIN_API_TOKEN
    if (adminToken) {
      config.headers['X-Admin-Token'] = adminToken
    }

    config.headers['X-Changed-By'] = 'agentic-fe'

    return config
  }

  private throwAdminErrorFromAxios(error: AxiosError): never {
    const response = error.response
    const body = response?.data as ApiResponse<AdminErrorPayload> | undefined

    if (body && typeof body === 'object' && 'success' in body && body.success === false) {
      const payload = body.data
      throw new AdminApiError(
        body.message || error.message,
        response?.status ?? 500,
        payload?.code,
        payload?.field ?? null,
      )
    }

    throw new AdminApiError(
      error.message || 'Request failed',
      response?.status ?? 500,
    )
  }

  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.axiosInstance.request(config)
      return unwrapEnvelope(response)
    } catch (error) {
      if (axios.isAxiosError(error)) {
        this.throwAdminErrorFromAxios(error)
      }
      throw error
    }
  }

  protected get<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url: endpoint })
  }

  protected post<T, D = unknown>(
    endpoint: string,
    data?: D,
    config?: AxiosRequestConfig<D>,
  ): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url: endpoint, data })
  }

  protected put<T, D = unknown>(
    endpoint: string,
    data?: D,
    config?: AxiosRequestConfig<D>,
  ): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url: endpoint, data })
  }

  protected patch<T, D = unknown>(
    endpoint: string,
    data?: D,
    config?: AxiosRequestConfig<D>,
  ): Promise<T> {
    return this.request<T>({ ...config, method: 'PATCH', url: endpoint, data })
  }

  protected deleteRequest<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url: endpoint })
  }
}
