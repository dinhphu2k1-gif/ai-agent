import { useRef, useEffect } from 'react'
import { Box, IconButton, Container } from '@mui/material'

interface ChatInputAreaProps {
  placeholder: string
  value: string
  onChange: (val: string) => void
  onSend: () => void
  disabled?: boolean
}

const ChatInputArea = ({ placeholder, value, onChange, onSend, disabled = false }: ChatInputAreaProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 128)}px`
    }
  }, [value])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (disabled) return
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 5,
        mb: 1,
      }}
    >
      <Container maxWidth="md" disableGutters sx={{ position: 'relative' }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: 1,
            bgcolor: 'surfaceContainerLowest',
            border: 1,
            borderColor: 'outlineVariant',
            borderRadius: 1,
            transition: 'all 0.15s',
            '&:focus-within': {
              borderColor: 'primary.main',
              boxShadow: '0 0 0 1px var(--mui-palette-primary-main)',
            },
          }}
        >
          <IconButton
            sx={{
              p: 1,
              color: 'onSurfaceVariant',
              borderRadius: 1,
              mb: 0.5,
              '&:hover': {
                bgcolor: 'surfaceContainerHigh',
                color: 'primary.main',
              },
            }}
          >
            <span className="material-symbols-outlined">add_circle</span>
          </IconButton>

          <Box
            component="textarea"
            ref={textareaRef}
            value={value}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            sx={{
              width: '100%',
              bgcolor: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'onSurface',
              fontFamily: 'Inter',
              fontSize: '14px',
              resize: 'none',
              p: 1,
              maxHeight: 128,
              minHeight: 36,
            }}
          />

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
            <IconButton
              title="Upload Data"
              sx={{
                p: 1,
                color: 'onSurfaceVariant',
                borderRadius: 1,
                '&:hover': {
                  bgcolor: 'surfaceContainerHigh',
                  color: 'secondary.main',
                },
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                attach_file
              </span>
            </IconButton>

            <IconButton
              onClick={onSend}
              disabled={disabled || !value.trim()}
              sx={{
                p: 1,
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                borderRadius: 1,
                boxShadow: 1,

                '&.Mui-disabled': {
                  bgcolor: 'surfaceContainerHighest',
                  color: 'onSurfaceVariant',
                  opacity: 0.5,
                },
              }}
            >
              <span
                className="material-symbols-outlined"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                send
              </span>
            </IconButton>
          </Box>
        </Box>
      </Container>
    </Box>
  )
}

export default ChatInputArea
