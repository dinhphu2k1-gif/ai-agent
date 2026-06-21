import { parseSqlResultBlock } from './parseSqlResultBlock'

import type {
  ActionButton,
  ActionPromptData,
  AgentMessageData,
  ExecutionTraceStep,
  Message,
  TableRow,
} from './types'

const ensureAgentData = (msg: Message): AgentMessageData => {
  if (!msg.agentData) {
    msg.agentData = { paragraphs: [] }
  }
  return msg.agentData
}

const updateMessageById = (
  messages: Message[],
  messageId: string,
  updater: (msg: Message) => Message,
): Message[] =>
  messages.map((msg) => (msg.id === messageId ? updater({ ...msg }) : msg))

const findLastOptimisticUserId = (messages: Message[]): string | undefined => {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const msg = messages[i]
    if (msg.sender === 'user' && msg.id.startsWith('pending-user-')) {
      return msg.id
    }
  }
  return undefined
}

export const applySseEvent = (
  messages: Message[],
  eventName: string,
  data: Record<string, unknown>,
  optimisticUserId?: string,
): Message[] => {
  switch (eventName) {
    case 'user.ack': {
      const messageId = String(data.messageId ?? '')
      const timestamp = data.timestamp ? String(data.timestamp) : undefined
      const targetId = optimisticUserId ?? findLastOptimisticUserId(messages)
      if (!targetId) return messages

      return messages.map((msg) =>
        msg.id === targetId
          ? { ...msg, id: messageId, timestamp: timestamp ?? msg.timestamp }
          : msg,
      )
    }

    case 'message.start': {
      const messageId = String(data.messageId ?? '')
      const timestamp = data.timestamp ? String(data.timestamp) : undefined
      if (messages.some((m) => m.id === messageId)) return messages

      return [
        ...messages,
        {
          id: messageId,
          sender: 'agent',
          timestamp,
          agentData: { paragraphs: [] },
        },
      ]
    }

    case 'trace.step': {
      const messageId = String(data.messageId ?? '')
      const step = data.step as ExecutionTraceStep | undefined
      if (!step) return messages

      return updateMessageById(messages, messageId, (msg) => {
        const agentData = ensureAgentData(msg)
        return {
          ...msg,
          agentData: {
            ...agentData,
            executionTrace: [...(agentData.executionTrace ?? []), step],
          },
        }
      })
    }

    case 'content.delta': {
      const messageId = String(data.messageId ?? '')
      const text = String(data.text ?? '')
      const paragraphIndex = Number(data.paragraphIndex ?? 0)

      return updateMessageById(messages, messageId, (msg) => {
        const agentData = ensureAgentData(msg)
        const paragraphs = [...agentData.paragraphs]
        while (paragraphs.length <= paragraphIndex) {
          paragraphs.push('')
        }
        paragraphs[paragraphIndex] = (paragraphs[paragraphIndex] ?? '') + text

        return {
          ...msg,
          agentData: { ...agentData, paragraphs },
        }
      })
    }

    case 'content.paragraph': {
      const messageId = String(data.messageId ?? '')
      const text = String(data.text ?? data.paragraph ?? '')
      const paragraphIndex = Number(data.paragraphIndex ?? 0)
      const parsedSql = parseSqlResultBlock(text)

      return updateMessageById(messages, messageId, (msg) => {
        const agentData = ensureAgentData(msg)
        const paragraphs = [...agentData.paragraphs]
        while (paragraphs.length <= paragraphIndex) {
          paragraphs.push('')
        }

        if (parsedSql) {
          paragraphs[paragraphIndex] = parsedSql.remainderText
          return {
            ...msg,
            agentData: {
              ...agentData,
              paragraphs: paragraphs.filter((p) => p.trim().length > 0),
              sqlQuery: parsedSql.sql,
              dataTable: parsedSql.dataTable,
            },
          }
        }

        paragraphs[paragraphIndex] = text

        return {
          ...msg,
          agentData: { ...agentData, paragraphs },
        }
      })
    }

    case 'table': {
      const messageId = String(data.messageId ?? '')

      return updateMessageById(messages, messageId, (msg) => {
        const agentData = ensureAgentData(msg)
        return {
          ...msg,
          agentData: {
            ...agentData,
            tableHeader: data.tableHeader ? String(data.tableHeader) : agentData.tableHeader,
            tableRows: (data.tableRows as TableRow[] | undefined) ?? agentData.tableRows,
          },
        }
      })
    }

    case 'action.buttons': {
      const messageId = String(data.messageId ?? '')

      return updateMessageById(messages, messageId, (msg) => {
        const agentData = ensureAgentData(msg)
        return {
          ...msg,
          agentData: {
            ...agentData,
            actionButtons: (data.buttons as ActionButton[] | undefined) ?? agentData.actionButtons,
          },
        }
      })
    }

    case 'action.prompt': {
      const messageId = String(data.messageId ?? '')
      const promptData = data.promptData as ActionPromptData | undefined
      if (!promptData) return messages
      if (messages.some((m) => m.id === messageId)) return messages

      return [
        ...messages,
        {
          id: messageId,
          sender: 'action_prompt',
          promptData,
        },
      ]
    }

    case 'message.end':
    case 'error':
    case 'run.failed':
    case 'run.start':
      return messages

    default:
      return messages
  }
}
