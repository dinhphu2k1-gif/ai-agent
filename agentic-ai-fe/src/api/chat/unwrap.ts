import type { AxiosResponse } from 'axios'

import type { ApiResponse } from '@/api/index'

import { ChatApiError } from './errors'
import type { ChatPageableResponse } from './types'

type ChatErrorPayload = {
  code?: string
}

export const unwrapEnvelope = <T>(response: AxiosResponse<ApiResponse<T>>): T => {
  const body = response.data

  if (!body.success) {
    const payload = body.data as ChatErrorPayload | undefined
    throw new ChatApiError(
      body.message || 'Request failed',
      response.status,
      payload?.code,
      body.data,
    )
  }

  return body.data
}

export const unwrapMessagesPage = <T>(page: ChatPageableResponse<T>): T[] => {
  if (!page.success) {
    throw new ChatApiError(page.message || 'Request failed', 200, undefined, page.data)
  }

  return page.data
}
