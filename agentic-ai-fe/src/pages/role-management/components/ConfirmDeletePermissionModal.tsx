import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  IconButton,
  Button,
} from '@mui/material'

interface ConfirmDeletePermissionModalProps {
  open: boolean
  permissionPath: string
  submitting?: boolean
  onClose: () => void
  onConfirm: () => void | Promise<void>
}

const ConfirmDeletePermissionModal = ({
  open,
  permissionPath,
  submitting = false,
  onClose,
  onConfirm,
}: ConfirmDeletePermissionModalProps) => {
  const handleConfirm = async () => {
    try {
      await onConfirm()
      onClose()
    } catch {
      // Parent shows toast; keep modal open
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
          <span className="material-symbols-outlined">warning</span>
        </Box>
        <Typography variant="headlineAgent" sx={{ flex: 1 }}>
          Remove permission
        </Typography>
        <IconButton onClick={onClose} size="small" aria-label="Close">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            close
          </span>
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 2 }}>
        <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant', pt: 2 }}>
          Remove permission for{' '}
          <Box component="span" sx={{ color: 'onSurface', fontWeight: 600, fontFamily: 'monospace' }}>
            {permissionPath}
          </Box>
          ? This cannot be undone.
        </Typography>
      </DialogContent>

      <DialogActions
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerLow)',
        }}
      >
        <Button onClick={onClose} variant="outlined" disabled={submitting} sx={{ textTransform: 'none' }}>
          Cancel
        </Button>
        <Button
          variant="contained"
          color="error"
          disabled={submitting}
          onClick={() => void handleConfirm()}
          sx={{ textTransform: 'none' }}
        >
          Remove
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ConfirmDeletePermissionModal
