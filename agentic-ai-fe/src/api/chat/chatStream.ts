import { getChatAccessToken } from './auth'
import { getChatApiBaseUrl } from './config'
import { ChatApiError, RunInProgressError } from './errors'
import type { ApiResponse } from '@/api/index'
import type { PostMessageRequest, SseHandler } from './types'

type ChatErrorPayload = {
  code?: string
  runId?: string
  channelId?: string
}

export interface StreamOptions {
  signal?: AbortSignal
  idempotencyKey?: string
  onEvent: SseHandler
}

const parseSseBlock = (block: string): { eventName: string; eventId?: string; data: Record<string, unknown> } | null => {
  if (!block.trim()) return null

  let eventName = 'message'
  let eventId: string | undefined
  let dataLine = ''

  for (const line of block.split('\n')) {
    if (line.startsWith('event: ')) eventName = line.slice(7).trim()
    else if (line.startsWith('id: ')) eventId = line.slice(4).trim()
    else if (line.startsWith('data: ')) dataLine = line.slice(6)
  }

  if (!dataLine) return null

  return {
    eventName,
    eventId,
    data: JSON.parse(dataLine) as Record<string, unknown>,
  }
}

const consumeSseStream = async (
  body: ReadableStream<Uint8Array>,
  onEvent: SseHandler,
  signal?: AbortSignal,
): Promise<void> => {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      if (signal?.aborted) {
        await reader.cancel()
        return
      }

      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''

      for (const block of parts) {
        const parsed = parseSseBlock(block)
        if (parsed) {
          onEvent(parsed.eventName, parsed.data, parsed.eventId)
        }
      }
    }

    if (buffer.trim()) {
      const parsed = parseSseBlock(buffer)
      if (parsed) {
        onEvent(parsed.eventName, parsed.data, parsed.eventId)
      }
    }
  } finally {
    reader.releaseLock()
  }
}

const throwHttpError = async (res: Response): Promise<never> => {
  let body: ApiResponse<ChatErrorPayload> | null = null

  try {
    body = (await res.json()) as ApiResponse<ChatErrorPayload>
  } catch {
    // ignore
  }

  if (body && body.success === false) {
    const payload = body.data
    if (payload?.code === 'RUN_IN_PROGRESS') {
      throw new RunInProgressError(body.message, payload.runId, payload.channelId)
    }

    throw new ChatApiError(body.message, res.status, payload?.code, body.data)
  }

  throw new ChatApiError(`HTTP ${res.status}`, res.status)
}

export const postMessageStream = async (
  channelId: string,
  body: PostMessageRequest,
  options: StreamOptions,
): Promise<void> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
    Authorization: `Bearer ${getChatAccessToken()}`,
  }

  if (options.idempotencyKey) {
    headers['Idempotency-Key'] = options.idempotencyKey
  }

  const res = await fetch(`${getChatApiBaseUrl()}/channels/${channelId}/messages`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal: options.signal,
  })

  if (!res.ok) {
    await throwHttpError(res)
  }

  if (!res.body) {
    throw new ChatApiError('Empty response body', res.status)
  }

  await consumeSseStream(res.body, options.onEvent, options.signal)
}

export const openRunStream = async (
  runId: string,
  options: StreamOptions & { lastEventId?: number },
): Promise<void> => {
  const params = new URLSearchParams()
  if (options.lastEventId !== undefined && options.lastEventId > 0) {
    params.set('lastEventId', String(options.lastEventId))
  }

  const query = params.toString()
  const url = `${getChatApiBaseUrl()}/runs/${runId}/stream${query ? `?${query}` : ''}`

  const headers: Record<string, string> = {
    Accept: 'text/event-stream',
    Authorization: `Bearer ${getChatAccessToken()}`,
  }

  if (options.lastEventId !== undefined && options.lastEventId > 0) {
    headers['Last-Event-ID'] = String(options.lastEventId)
  }

  const res = await fetch(url, {
    method: 'GET',
    headers,
    signal: options.signal,
  })

  if (!res.ok) {
    await throwHttpError(res)
  }

  if (!res.body) {
    throw new ChatApiError('Empty response body', res.status)
  }

  await consumeSseStream(res.body, options.onEvent, options.signal)
}
