import { useEffect, useState } from 'react'

import { chatApi, getChatErrorMessage, isAbortError } from '@/api/chat'
import type { Message } from '@/api/chat'

import { sortMessagesChronologically } from '../helpers/sortMessagesChronologically'

interface UseChatMessagesOptions {
  channelId: string
  onMessagesLoaded: (messages: Message[]) => void
}

export const useChatMessages = ({ channelId, onMessagesLoaded }: UseChatMessagesOptions) => {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    let cancelled = false

    const load = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const items = await chatApi.listMessages(channelId, 1, 50, {
          signal: controller.signal,
        })
        if (!cancelled) onMessagesLoaded(sortMessagesChronologically(items))
      } catch (err) {
        if (isAbortError(err) || cancelled) return
        if (!cancelled) {
          setError(getChatErrorMessage(err))
          onMessagesLoaded([])
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    load()

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [channelId, onMessagesLoaded])

  return { isLoading, error }
}
