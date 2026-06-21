import { Box, Typography } from '@mui/material'

interface SystemMessageProps {
  content: string
}

const SystemMessage = ({ content }: SystemMessageProps) => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        py: 1,
      }}
    >
      <Box
        sx={{
          px: 2,
          py: 1,
          borderRadius: 1,
          bgcolor: 'surfaceContainerLow',
          border: 1,
          borderColor: 'outlineVariant',
          maxWidth: '90%',
        }}
      >
        <Typography
          variant="caption"
          sx={{ color: 'onSurfaceVariant', whiteSpace: 'pre-wrap', textAlign: 'center', display: 'block' }}
        >
          {content}
        </Typography>
      </Box>
    </Box>
  )
}

export default SystemMessage
