import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  IconButton,
  Button,
  Stack,
} from '@mui/material'

interface ConfirmDeleteChannelModalProps {
  open: boolean
  channelTitle: string
  submitting?: boolean
  onClose: () => void
  onConfirm: () => void | Promise<void>
}

const ConfirmDeleteChannelModal = ({
  open,
  channelTitle,
  submitting = false,
  onClose,
  onConfirm,
}: ConfirmDeleteChannelModalProps) => {
  const handleConfirm = async () => {
    try {
      await onConfirm()
      onClose()
    } catch {
      // Parent shows toast
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xs"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            bgcolor: 'var(--mui-palette-surfaceContainer)',
            backgroundImage: 'none',
            borderRadius: 2,
            border: 1,
            borderColor: 'var(--mui-palette-outlineVariant)',
          },
        },
      }}
    >
      <DialogTitle
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          borderBottom: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerHigh)',
        }}
      >
        <Box sx={{ color: 'var(--mui-palette-error)', display: 'flex' }}>
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
            warning
          </span>
        </Box>
        <Typography variant="headlineAgent" sx={{ flex: 1 }}>
          Delete channel
        </Typography>
        <IconButton onClick={onClose} size="small" sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            close
          </span>
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 2, bgcolor: 'var(--mui-palette-surfaceContainer)' }}>
        <Stack spacing={1.5} sx={{ pt: 1 }}>
          <Typography variant="bodyMain" sx={{ color: 'var(--mui-palette-onSurface)' }}>
            Delete <strong>{channelTitle}</strong>? Message history for this channel will be removed.
          </Typography>
          <Typography variant="caption" sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}>
            This action cannot be undone.
          </Typography>
        </Stack>
      </DialogContent>

      <DialogActions
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerLow)',
          gap: 1,
        }}
      >
        <Button onClick={onClose} sx={{ color: 'var(--mui-palette-onSurfaceVariant)', textTransform: 'none' }}>
          Cancel
        </Button>
        <Button
          variant="contained"
          color="error"
          disabled={submitting}
          onClick={() => void handleConfirm()}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ConfirmDeleteChannelModal
