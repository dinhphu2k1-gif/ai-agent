import { Box, Typography } from '@mui/material'

interface UserMessageProps {
  content: string
}

const UserMessage = ({ content }: UserMessageProps) => {
  return (
    <Box
      sx={{
        display: 'flex',
        gap: 'var(--mui-spacing-stack-sm)',
        alignSelf: 'flex-end',
        maxWidth: '85%',
        '@keyframes fadeIn': {
          from: { opacity: 0, transform: 'translateY(8px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
        animation: 'fadeIn 0.25s ease-out forwards',
      }}
    >
      <Box
        sx={{
          bgcolor: 'surfaceContainerHigh',
          px: 2,
          py: 1.5,
          borderRadius: 2,
          borderTopRightRadius: 0,
          border: 1,
          borderColor: 'outlineVariant',
          color: 'onSurface',
        }}
      >
        <Typography variant="bodyMain" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
          {content}
        </Typography>
      </Box>
    </Box>
  )
}

export default UserMessage
