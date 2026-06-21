import { useCallback, useEffect, useRef, useState } from 'react'

import {
  applySseEvent,
  getChatErrorMessage,
  isAbortError,
  postMessageStream,
  RunInProgressError,
} from '@/api/chat'
import type { Message, PostMessageRequest } from '@/api/chat'

import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'

import { formatMessageTime } from '../helpers/formatMessageTime'

interface UseChatStreamOptions {
  channelId: string
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
}

const stripActionPrompts = (messages: Message[]): Message[] =>
  messages.filter((msg) => msg.sender !== 'action_prompt')

export const useChatStream = ({ channelId, setMessages }: UseChatStreamOptions) => {
  const dispatch = useAppDispatch()
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const optimisticUserIdRef = useRef<string | undefined>(undefined)
  const lastEventIdRef = useRef(0)

  const showError = useCallback(
    (message: string) => {
      dispatch(setAlert({ children: message, severity: 'error' }))
    },
    [dispatch],
  )

  const abortStream = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setIsStreaming(false)
  }, [])

  useEffect(() => {
    return () => {
      abortStream()
    }
  }, [abortStream, channelId])

  const runStream = useCallback(
    async (body: PostMessageRequest) => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      setIsStreaming(true)
      lastEventIdRef.current = 0

      try {
        await postMessageStream(channelId, body, {
          signal: controller.signal,
          onEvent: (eventName, data, eventId) => {
            if (eventId) {
              const idNum = Number(eventId)
              if (!Number.isNaN(idNum) && idNum > lastEventIdRef.current) {
                lastEventIdRef.current = idNum
              }
            }

            if (eventName === 'error') {
              showError(String(data.message ?? 'Agent error'))
            }

            if (eventName === 'run.failed') {
              showError(String(data.message ?? 'Run failed'))
              setIsStreaming(false)
            }

            if (eventName === 'message.end') {
              setIsStreaming(false)
            }

            setMessages((prev) =>
              applySseEvent(prev, eventName, data, optimisticUserIdRef.current),
            )
          },
        })
      } catch (err) {
        if (isAbortError(err)) return

        if (err instanceof RunInProgressError) {
          showError(getChatErrorMessage(err))
        } else {
          showError(getChatErrorMessage(err))
        }
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null
        }
        setIsStreaming(false)
      }
    },
    [channelId, setMessages, showError],
  )

  const sendText = useCallback(
    async (content: string) => {
      const trimmed = content.trim()
      if (!trimmed || isStreaming) return

      const optimisticId = `pending-user-${Date.now()}`
      optimisticUserIdRef.current = optimisticId

      setMessages((prev) => {
        const cleared = stripActionPrompts(prev)
        return [
          ...cleared,
          {
            id: optimisticId,
            sender: 'user',
            content: trimmed,
            timestamp: formatMessageTime(new Date().toISOString()),
          },
        ]
      })

      await runStream({ type: 'text', content: trimmed })
    },
    [isStreaming, runStream, setMessages],
  )

  const sendAction = useCallback(
    async (actionId: string, label: string, replyToMessageId?: string) => {
      if (isStreaming) return

      const optimisticId = `pending-user-${Date.now()}`
      optimisticUserIdRef.current = optimisticId

      setMessages((prev) => {
        const cleared = stripActionPrompts(prev)
        return [
          ...cleared,
          {
            id: optimisticId,
            sender: 'user',
            content: label,
            timestamp: formatMessageTime(new Date().toISOString()),
          },
        ]
      })

      await runStream({
        type: 'action',
        actionId,
        label,
        replyToMessageId,
      })
    },
    [isStreaming, runStream, setMessages],
  )

  return {
    isStreaming,
    sendText,
    sendAction,
    abortStream,
  }
}
