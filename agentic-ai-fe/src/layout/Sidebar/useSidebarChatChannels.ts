import { useCallback, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { getChatErrorMessage } from '@/api/chat'
import type { Channel } from '@/api/chat'
import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'
import type { CreateChannelFormData } from '@/pages/chat/components/CreateChannelDialog'
import { useChatChannelsContext } from '@/pages/chat/context/ChatChannelsContext'

const DEFAULT_CHANNEL_ID = 'market-trends'

export const useSidebarChatChannels = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const location = useLocation()

  const activeChannelIdOnRoute = useMemo(() => {
    if (!location.pathname.startsWith('/chat')) return null
    const match = location.pathname.match(/^\/chat\/([^/]+)/)
    return match?.[1] ?? DEFAULT_CHANNEL_ID
  }, [location.pathname])

  const { channels, createChannel, deleteChannel, isCreating, isDeleting } = useChatChannelsContext()

  const [createOpen, setCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Channel | null>(null)

  const handleOpenCreate = useCallback(() => {
    setCreateOpen(true)
  }, [])

  const handleCreateChannel = useCallback(
    async (data: CreateChannelFormData) => {
      try {
        const created = await createChannel({ title: data.title, icon: 'forum' })
        dispatch(setAlert({ children: 'Channel created', severity: 'success' }))
        navigate(`/chat/${created.id}`)
      } catch (error) {
        dispatch(setAlert({ children: getChatErrorMessage(error), severity: 'error' }))
        throw error
      }
    },
    [createChannel, dispatch, navigate],
  )

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteTarget) return

    const deletedId = deleteTarget.id
    const remaining = channels.filter((ch) => ch.id !== deletedId)
    const nextChannel = remaining[0]

    try {
      await deleteChannel(deletedId)
      dispatch(setAlert({ children: 'Channel deleted', severity: 'success' }))

      if (activeChannelIdOnRoute && deletedId === activeChannelIdOnRoute) {
        navigate(nextChannel ? `/chat/${nextChannel.id}` : '/chat')
      }
    } catch (error) {
      dispatch(setAlert({ children: getChatErrorMessage(error), severity: 'error' }))
      throw error
    }
  }, [activeChannelIdOnRoute, channels, deleteChannel, deleteTarget, dispatch, navigate])

  return {
    createOpen,
    setCreateOpen,
    deleteTarget,
    setDeleteTarget,
    isCreating,
    isDeleting,
    handleOpenCreate,
    handleCreateChannel,
    handleConfirmDelete,
  }
}
