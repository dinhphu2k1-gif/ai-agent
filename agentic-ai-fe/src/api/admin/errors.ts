import axios from 'axios'

const ADMIN_ERROR_MESSAGES: Record<string, string> = {
  NOT_FOUND: 'The requested resource was not found',
  GROUP_NAME_CONFLICT: 'A group with this name already exists',
  ROLE_NAME_CONFLICT: 'A role with this name already exists',
  ENTITY_IN_USE: 'Cannot delete: resource is still in use',
  PERMISSION_NOT_DIRECT: 'This permission is inherited and cannot be changed here',
}

export class AdminApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public field?: string | null,
  ) {
    super(message)
    this.name = 'AdminApiError'
  }
}

export const getAdminErrorMessage = (error: unknown): string => {
  if (error instanceof AdminApiError) {
    if (error.code && ADMIN_ERROR_MESSAGES[error.code]) {
      return ADMIN_ERROR_MESSAGES[error.code]
    }
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
