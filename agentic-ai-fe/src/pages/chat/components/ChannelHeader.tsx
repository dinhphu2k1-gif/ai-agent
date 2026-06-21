import { Box, IconButton } from '@mui/material'

interface ChannelHeaderProps {
  channelName: string
  onDelete?: () => void
  deleteDisabled?: boolean
}

const ChannelHeader = ({ channelName, onDelete, deleteDisabled = false }: ChannelHeaderProps) => {
  return (
    <Box
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 0.5,
        py: 1.5,
        bgcolor: 'transparent',
        zIndex: 10,
        flexShrink: 0,
      }}
    >
      <Box
        sx={{
          backdropFilter: 'blur(8px)',
          px: 1.5,
          py: 0.5,
          borderRadius: 9999,
          border: 1,
          borderColor: 'outlineVariant',
          color: 'onSurfaceVariant',
          fontFamily: 'JetBrains Mono',
          fontSize: '12px',
        }}
      >
        Channel: {channelName} Initialized
      </Box>
      {onDelete && (
        <IconButton
          size="small"
          aria-label="Delete channel"
          disabled={deleteDisabled}
          onClick={onDelete}
          sx={{
            bgcolor: 'surfaceContainer',
            border: 1,
            borderColor: 'outlineVariant',
            color: 'onSurfaceVariant',
            '&:hover': { color: 'error.main', borderColor: 'error.main' },
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
            delete
          </span>
        </IconButton>
      )}
    </Box>
  )
}

export default ChannelHeader
