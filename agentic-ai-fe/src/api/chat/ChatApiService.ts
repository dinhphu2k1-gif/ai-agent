import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

import type { ApiResponse } from '@/api/index'

import { getChatAccessToken } from './auth'
import { getChatApiBaseUrl } from './config'
import { ChatApiError, RunInProgressError } from './errors'
import type {
  Channel,
  ChatPageableResponse,
  CreateChannelRequest,
  Message,
  PostMessageAsyncData,
  PostMessageRequest,
  UploadAttachmentData,
} from './types'
import { unwrapEnvelope, unwrapMessagesPage } from './unwrap'

type ChatErrorPayload = {
  code?: string
  runId?: string
  channelId?: string
  retryAfterSec?: number
}

class ChatApiService {
  protected axiosInstance: AxiosInstance

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: getChatApiBaseUrl(),
      timeout: 60000,
    })
    this.axiosInstance.interceptors.request.use(this.applyAuthHeaders)
  }

  private applyAuthHeaders(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
    const headers = axios.AxiosHeaders.from(config.headers ?? {})
    headers.set('Authorization', `Bearer ${getChatAccessToken()}`)
    config.headers = headers
    return config
  }

  private throwChatErrorFromAxios(error: AxiosError): never {
    const response = error.response
    const body = response?.data as ApiResponse<ChatErrorPayload> | undefined

    if (body && typeof body === 'object' && 'success' in body && body.success === false) {
      const payload = body.data
      if (payload?.code === 'RUN_IN_PROGRESS') {
        throw new RunInProgressError(
          body.message || error.message,
          payload.runId,
          payload.channelId,
        )
      }

      throw new ChatApiError(
        body.message || error.message,
        response?.status ?? 500,
        payload?.code,
        body.data,
      )
    }

    throw new ChatApiError(error.message || 'Request failed', response?.status ?? 500)
  }

  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.axiosInstance.request(config)
      return unwrapEnvelope(response)
    } catch (error) {
      if (axios.isAxiosError(error)) {
        this.throwChatErrorFromAxios(error)
      }
      throw error
    }
  }

  private async requestPage<T>(
    config: AxiosRequestConfig,
  ): Promise<{ items: T[]; currentPage: number; totalItems: number; totalPages: number }> {
    try {
      const response: AxiosResponse<ChatPageableResponse<T>> =
        await this.axiosInstance.request(config)
      const page = response.data
      const items = unwrapMessagesPage(page)

      return {
        items,
        currentPage: page.currentPage,
        totalItems: page.totalItems,
        totalPages: page.totalPages,
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        this.throwChatErrorFromAxios(error)
      }
      throw error
    }
  }

  listChannels(config?: AxiosRequestConfig): Promise<Channel[]> {
    return this.request<Channel[]>({ ...config, method: 'GET', url: '/channels' })
  }

  createChannel(body: CreateChannelRequest, config?: AxiosRequestConfig): Promise<Channel> {
    return this.request<Channel>({
      ...config,
      method: 'POST',
      url: '/channels',
      data: body,
    })
  }

  async deleteChannel(channelId: string, config?: AxiosRequestConfig): Promise<void> {
    try {
      const response = await this.axiosInstance.request({
        ...config,
        method: 'DELETE',
        url: `/channels/${channelId}`,
      })

      if (response.status === 204) return

      const body = response.data as ApiResponse<unknown> | undefined
      if (body && typeof body === 'object' && 'success' in body && body.success === false) {
        throw new ChatApiError(
          body.message || 'Request failed',
          response.status,
          (body.data as ChatErrorPayload | undefined)?.code,
          body.data,
        )
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        this.throwChatErrorFromAxios(error)
      }
      throw error
    }
  }

  listMessages(
    channelId: string,
    page = 1,
    pageSize = 50,
    config?: AxiosRequestConfig,
  ): Promise<Message[]> {
    return this.requestPage<Message>({
      ...config,
      method: 'GET',
      url: `/channels/${channelId}/messages`,
      params: { page, pageSize },
    }).then((result) => result.items)
  }

  getMessage(messageId: string, config?: AxiosRequestConfig): Promise<Message> {
    return this.request<Message>({ ...config, method: 'GET', url: `/messages/${messageId}` })
  }

  postMessageAsync(
    channelId: string,
    body: PostMessageRequest,
    config?: AxiosRequestConfig,
  ): Promise<PostMessageAsyncData> {
    return this.request<PostMessageAsyncData>({
      ...config,
      method: 'POST',
      url: `/channels/${channelId}/messages`,
      params: { async: true },
      data: body,
      headers: {
        Accept: 'application/json',
        ...(config?.headers ?? {}),
      },
    })
  }

  uploadAttachment(
    channelId: string,
    file: File,
    config?: AxiosRequestConfig,
  ): Promise<UploadAttachmentData> {
    const formData = new FormData()
    formData.append('file', file)

    return this.request<UploadAttachmentData>({
      ...config,
      method: 'POST',
      url: `/channels/${channelId}/attachments`,
      data: formData,
      headers: {
        ...(config?.headers ?? {}),
      },
    })
  }
}

export default new ChatApiService()
