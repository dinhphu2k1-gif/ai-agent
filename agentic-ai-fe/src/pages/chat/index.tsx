import { useCallback, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, CircularProgress, Typography } from '@mui/material'

import { getChatErrorMessage } from '@/api/chat'
import type { Message } from '@/api/chat'
import { useAppDispatch } from '@/redux/hooks'
import { setAlert } from '@/redux/reducers/AlertSlice'

import ChatWorkspace from './components/ChatWorkspace'
import ChatInputArea from './components/ChatInputArea'
import ChannelHeader from './components/ChannelHeader'
import ConfirmDeleteChannelModal from './components/ConfirmDeleteChannelModal'
import { useChatChannels } from './hooks/useChatChannels'
import { useChatMessages } from './hooks/useChatMessages'
import { useChatStream } from './hooks/useChatStream'

const ChatPage = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { channelId } = useParams<{ channelId: string }>()
  const activeChannelId = channelId || 'market-trends'

  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [deleteOpen, setDeleteOpen] = useState(false)

  const { channelTitle, activeChannel, channels, deleteChannel, isDeleting } =
    useChatChannels(activeChannelId)

  const handleMessagesLoaded = useCallback((loaded: Message[]) => {
    setMessages(loaded)
  }, [])

  const { isLoading: isLoadingHistory, error: historyError } = useChatMessages({
    channelId: activeChannelId,
    onMessagesLoaded: handleMessagesLoaded,
  })

  const { isStreaming, sendText, sendAction } = useChatStream({
    channelId: activeChannelId,
    setMessages,
  })

  const handleSelectOption = (optionId: string, optionLabel: string) => {
    if (optionId === 'custom') {
      setMessages((prev) => prev.filter((msg) => msg.sender !== 'action_prompt'))
      return
    }

    const promptMessage = messages.find((msg) => msg.sender === 'action_prompt')
    void sendAction(optionId, optionLabel, promptMessage?.id)
  }

  const handleSendMessage = () => {
    if (!inputValue.trim() || isStreaming) return
    const text = inputValue
    setInputValue('')
    void sendText(text)
  }

  const inputDisabled = isStreaming || isLoadingHistory

  const handleConfirmDeleteChannel = useCallback(async () => {
    const remaining = channels.filter((ch) => ch.id !== activeChannelId)
    try {
      await deleteChannel(activeChannelId)
      dispatch(setAlert({ children: 'Channel deleted', severity: 'success' }))
      const next = remaining[0]
      navigate(next ? `/chat/${next.id}` : '/chat')
    } catch (error) {
      dispatch(setAlert({ children: getChatErrorMessage(error), severity: 'error' }))
      throw error
    }
  }, [activeChannelId, channels, deleteChannel, dispatch, navigate])

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        bgcolor: 'background.default',
        position: 'relative',
      }}
    >
      <ChannelHeader
        channelName={channelTitle}
        onDelete={() => setDeleteOpen(true)}
        deleteDisabled={isDeleting || isStreaming}
      />

      {isLoadingHistory ? (
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CircularProgress size={32} />
        </Box>
      ) : (
        <>
          {historyError && (
            <Box sx={{ px: 2, py: 1, textAlign: 'center' }}>
              <Typography variant="caption" sx={{ color: 'error.main' }}>
                {historyError}
              </Typography>
            </Box>
          )}
          <ChatWorkspace messages={messages} onSelectOption={handleSelectOption} />
        </>
      )}

      <ChatInputArea
        placeholder={`Message ${channelTitle}...`}
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSendMessage}
        disabled={inputDisabled}
      />

      <ConfirmDeleteChannelModal
        open={deleteOpen}
        channelTitle={activeChannel.title}
        submitting={isDeleting}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleConfirmDeleteChannel}
      />
    </Box>
  )
}

export default ChatPage
