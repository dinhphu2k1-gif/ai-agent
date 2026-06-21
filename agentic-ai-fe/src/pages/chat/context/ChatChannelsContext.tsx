import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { chatApi, getChatErrorMessage, isAbortError } from '@/api/chat'
import type { Channel, CreateChannelRequest } from '@/api/chat'

export interface ChatChannelsContextValue {
  channels: Channel[]
  isLoading: boolean
  error: string | null
  isCreating: boolean
  isDeleting: boolean
  refetch: () => Promise<void>
  createChannel: (body: CreateChannelRequest) => Promise<Channel>
  deleteChannel: (channelId: string) => Promise<void>
}

const ChatChannelsContext = createContext<ChatChannelsContextValue | null>(null)

export const ChatChannelsProvider = ({ children }: { children: ReactNode }) => {
  const [channels, setChannels] = useState<Channel[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const refetch = useCallback(async () => {
    const controller = new AbortController()
    try {
      setIsLoading(true)
      setError(null)
      const data = await chatApi.listChannels({ signal: controller.signal })
      setChannels(data)
    } catch (err) {
      if (isAbortError(err)) return
      setError(getChatErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    let cancelled = false

    const load = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await chatApi.listChannels({ signal: controller.signal })
        if (!cancelled) setChannels(data)
      } catch (err) {
        if (isAbortError(err) || cancelled) return
        if (!cancelled) setError(getChatErrorMessage(err))
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void load()

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [])

  const createChannel = useCallback(async (body: CreateChannelRequest) => {
    setIsCreating(true)
    try {
      const created = await chatApi.createChannel(body)
      setChannels((prev) => {
        if (prev.some((ch) => ch.id === created.id)) return prev
        return [...prev, created]
      })
      return created
    } finally {
      setIsCreating(false)
    }
  }, [])

  const deleteChannel = useCallback(async (channelId: string) => {
    setIsDeleting(true)
    try {
      await chatApi.deleteChannel(channelId)
      setChannels((prev) => prev.filter((ch) => ch.id !== channelId))
    } finally {
      setIsDeleting(false)
    }
  }, [])

  const value = useMemo(
    () => ({
      channels,
      isLoading,
      error,
      isCreating,
      isDeleting,
      refetch,
      createChannel,
      deleteChannel,
    }),
    [channels, isLoading, error, isCreating, isDeleting, refetch, createChannel, deleteChannel],
  )

  return <ChatChannelsContext.Provider value={value}>{children}</ChatChannelsContext.Provider>
}

export const useChatChannelsContext = (): ChatChannelsContextValue => {
  const ctx = useContext(ChatChannelsContext)
  if (!ctx) {
    throw new Error('useChatChannelsContext must be used within ChatChannelsProvider')
  }
  return ctx
}
