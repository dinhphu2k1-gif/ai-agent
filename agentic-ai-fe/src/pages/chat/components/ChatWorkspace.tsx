import { useEffect, useRef } from 'react'
import { Box, Container } from '@mui/material'
import type { Message } from '../types'
import UserMessage from './UserMessage'
import AgentMessage from './AgentMessage'
import ActionPromptCard from './ActionPromptCard'
import SystemMessage from './SystemMessage'

interface ChatWorkspaceProps {
  messages: Message[]
  onSelectOption: (optionId: string, optionLabel: string) => void
}

const ChatWorkspace = ({ messages, onSelectOption }: ChatWorkspaceProps) => {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <Box
      sx={{
        flex: 1,
        overflowY: 'auto',
        p: 'var(--mui-spacing-inset-standard)',
        pt: 8,
        pb: '140px',
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
      }}
    >
      <Container
        maxWidth="md"
        disableGutters
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {messages.map((msg) => {
          if (msg.sender === 'user') {
            return <UserMessage key={msg.id} content={msg.content || ''} />
          }

          if (msg.sender === 'agent' && msg.agentData) {
            return (
              <AgentMessage key={msg.id} agentData={msg.agentData} onActionClick={onSelectOption} />
            )
          }

          if (msg.sender === 'action_prompt' && msg.promptData) {
            return (
              <ActionPromptCard
                key={msg.id}
                promptData={msg.promptData}
                onSelectOption={onSelectOption}
              />
            )
          }

          if (msg.sender === 'system' && msg.content) {
            return <SystemMessage key={msg.id} content={msg.content} />
          }

          return null
        })}
        <div ref={bottomRef} />
      </Container>
    </Box>
  )
}

export default ChatWorkspace
