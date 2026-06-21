import type { AxiosResponse } from 'axios'

import type { ApiResponse } from '@/api/index'
import type { PageableResponse } from '@/types/type'

import { AdminApiError } from './errors'

type AdminErrorPayload = {
  code?: string
  field?: string | null
}

export const unwrapEnvelope = <T>(response: AxiosResponse<ApiResponse<T>>): T => {
  const body = response.data

  if (!body.success) {
    const payload = body.data as AdminErrorPayload | undefined
    throw new AdminApiError(
      body.message || 'Request failed',
      response.status,
      payload?.code,
      payload?.field ?? null,
    )
  }

  return body.data
}

export const unwrapPage = <T>(page: PageableResponse<T>): { items: T[]; page: PageableResponse<T> } => ({
  items: page.data,
  page,
})
