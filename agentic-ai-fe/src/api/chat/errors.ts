import axios from 'axios'

export class ChatApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public payload?: unknown,
  ) {
    super(message)
    this.name = 'ChatApiError'
  }
}

export class RunInProgressError extends ChatApiError {
  constructor(
    message: string,
    public runId?: string,
    public channelId?: string,
  ) {
    super(message, 409, 'RUN_IN_PROGRESS', { runId, channelId })
    this.name = 'RunInProgressError'
  }
}

export const getChatErrorMessage = (error: unknown): string => {
  if (error instanceof RunInProgressError) {
    return 'An agent run is already in progress for this channel. Please wait.'
  }
  if (error instanceof ChatApiError) {
    if (error.code === 'RATE_LIMITED') return error.message || 'Too many requests. Please wait.'
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Unexpected error'
}

export const isAbortError = (error: unknown): boolean => {
  if (axios.isCancel(error)) return true
  if (error instanceof Error && error.name === 'AbortError') return true
  if (error instanceof Error && error.name === 'CanceledError') return true
  return false
}
