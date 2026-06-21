import { useMemo } from 'react'

import type { Channel } from '@/api/chat'

import { useChatChannelsContext } from '../context/ChatChannelsContext'

const DEFAULT_CHANNEL_TITLE = 'Insight Workspace'

export const useChatChannels = (activeChannelId: string) => {
  const { channels, isLoading, error, isCreating, isDeleting, createChannel, deleteChannel, refetch } =
    useChatChannelsContext()

  const activeChannel = useMemo(
    () =>
      channels.find((ch) => ch.id === activeChannelId) ??
      ({
        id: activeChannelId,
        title: DEFAULT_CHANNEL_TITLE,
        icon: 'forum',
      } satisfies Channel),
    [channels, activeChannelId],
  )

  return {
    channels,
    activeChannel,
    channelTitle: activeChannel.title || DEFAULT_CHANNEL_TITLE,
    isLoading,
    error,
    isCreating,
    isDeleting,
    createChannel,
    deleteChannel,
    refetch,
  }
}
