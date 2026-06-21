import axios, {
  type InternalAxiosRequestConfig,
  type AxiosError,
  type AxiosInstance,
  type AxiosResponse,
  type AxiosRequestConfig,
} from 'axios'

import { handleException } from '@/utils'
import type { AuthenInfo } from '@/types/type'
import { loginUrl } from '@/types/constant'

import { store } from '@/redux'
import { setAlert } from '@/redux/reducers/AlertSlice'

// Define api data
export type ApiResponse<T> = {
  message: string
  success: boolean
  data: T
}

export class ApiService {
  protected axiosInstance: AxiosInstance
  constructor(baseUrl: string | undefined) {
    this.axiosInstance = axios.create({
      baseURL: baseUrl,
      timeout: 60000,
    })
    this.axiosInstance.interceptors.request.use(this.configInterceptorsRequest)
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      this.configInterceptorsResponse
    )
  }

  protected configInterceptorsRequest(
    config: InternalAxiosRequestConfig
  ): InternalAxiosRequestConfig {
    // set token for headers
    if (config.headers) {
      const cookies: AuthenInfo | undefined = {
        accessToken: 'test'
      }

      if (cookies) {
        config.headers.Authorization = `Bearer ${cookies.accessToken}`
      }
      config.headers['Access-Control-Allow-Origin'] = '*'
    }
    return config
  }

  protected configInterceptorsResponse(error: AxiosError) {
    const { response, config } = error
    const isHandleException = config?.headers['x-exception']

    if (response?.status === 403) {
      window.location.replace(loginUrl)
    }

    if (isHandleException) {
      const message = handleException(error)
      store.dispatch(setAlert({ children: message, severity: 'error' }))
      return Promise.resolve(error)
    }
    return Promise.reject(error)
  }

  public async get<T>(
    endpoint: string,
    config?: AxiosRequestConfig,
    handleException: boolean = true
  ): Promise<AxiosResponse<T>> {
    const response = await this.axiosInstance.get<T>(endpoint, {
      ...config,
      headers: { 'x-exception': handleException },
    })
    return response
  }

  public async post<T, D = unknown>(
    endpoint: string,
    data?: D,
    config?: AxiosRequestConfig<D>,
    handleException: boolean = true
  ): Promise<AxiosResponse<T>> {
    const response: AxiosResponse<T> = await this.axiosInstance.post<T>(
      endpoint,
      data,
      {
        ...config,
        headers: { 'x-exception': handleException },
      }
    )
    return response
  }

  public async put<T, D = unknown>(
    endpoint: string,
    data?: D,
    config?: AxiosRequestConfig<D>,
    handleException: boolean = true
  ): Promise<AxiosResponse<T>> {
    const response: AxiosResponse<T> = await this.axiosInstance.put<T>(
      endpoint,
      data,
      {
        ...config,
        headers: { 'x-exception': handleException },
      }
    )
    return response
  }

  public async delete<T>(
    endpoint: string,
    handleException: boolean = true,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse<T>> {
    const response: AxiosResponse<T> = await this.axiosInstance.delete<T>(
      endpoint,
      {
        ...config,
        headers: { 'x-exception': handleException },
      }
    )
    return response
  }
}
