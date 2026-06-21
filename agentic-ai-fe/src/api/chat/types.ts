import type { ApiResponse } from '@/api/index'

export type MessageSender = 'user' | 'agent' | 'system' | 'action_prompt'

export interface ExecutionTraceStep {
  title: string
  description: string
  icon: string
}

export interface TableRow {
  region: string
  actual: string
  projected: string
  variance: string
  isPositive: boolean
}

export interface DataTableColumn {
  key: string
  label: string
}

export interface DataTable {
  title?: string
  columns: DataTableColumn[]
  rows: Record<string, string>[]
}

export interface ActionButton {
  label: string
  icon: string
  actionId: string
}

export interface AgentMessageData {
  executionTrace?: ExecutionTraceStep[]
  paragraphs: string[]
  /** Parsed SQL query (from markdown sql fence) */
  sqlQuery?: string
  /** Dynamic columns from SQL preview or normalized legacy table */
  dataTable?: DataTable
  tableHeader?: string
  tableRows?: TableRow[]
  actionButtons?: ActionButton[]
}

export interface ActionPromptOption {
  label: string
  actionId: string
}

export interface ActionPromptData {
  title: string
  description: string
  options: ActionPromptOption[]
  customOptionLabel?: string
}

export interface AttachmentMeta {
  id: string
  fileName: string
  mimeType: string
  sizeBytes: number
}

export interface Message {
  id: string
  sender: MessageSender
  timestamp?: string
  content?: string
  agentData?: AgentMessageData
  promptData?: ActionPromptData
  attachments?: AttachmentMeta[]
}

export interface Channel {
  id: string
  title: string
  icon: string
  category?: string | null
}

/** POST /channels — create a user-owned chat channel */
export interface CreateChannelRequest {
  title: string
  icon?: string
}

export interface PostMessageRequest {
  type: 'text' | 'action'
  content?: string
  actionId?: string
  label?: string
  replyToMessageId?: string
  attachmentIds?: string[]
}

export interface ChatPageableResponse<T> extends ApiResponse<T[]> {
  currentPage: number
  totalItems: number
  totalPages: number
}

export interface PostMessageAsyncData {
  runId: string
  userMessageId: string
}

export interface UploadAttachmentData {
  attachmentId: string
  fileName: string
  mimeType: string
  sizeBytes: number
}

export type SseHandler = (
  eventName: string,
  data: Record<string, unknown>,
  eventId?: string,
) => void
