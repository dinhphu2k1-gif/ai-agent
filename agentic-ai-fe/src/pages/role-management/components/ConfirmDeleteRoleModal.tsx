import {
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  IconButton,
  Button,
} from '@mui/material'

interface ConfirmDeleteRoleModalProps {
  open: boolean
  roleName: string
  errorMessage?: string | null
  submitting?: boolean
  onClose: () => void
  onConfirm: () => void | Promise<void>
}

const ConfirmDeleteRoleModal = ({
  open,
  roleName,
  errorMessage = null,
  submitting = false,
  onClose,
  onConfirm,
}: ConfirmDeleteRoleModalProps) => {
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
          Delete role
        </Typography>
        <IconButton onClick={onClose} size="small" aria-label="Close">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            close
          </span>
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 2 }}>
        <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant', pt: 2 }}>
          Delete role{' '}
          <Box component="span" sx={{ color: 'onSurface', fontWeight: 600 }}>
            {roleName}
          </Box>
          ? Users and groups assigned to this role will lose it. This cannot be undone.
        </Typography>
        {errorMessage ? (
          <Alert severity="error" sx={{ mt: 2 }}>
            {errorMessage}
          </Alert>
        ) : null}
      </DialogContent>

      <DialogActions
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerLow)',
        }}
      >
        <Button
          onClick={onClose}
          variant="outlined"
          disabled={submitting}
          sx={{ textTransform: 'none' }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          color="error"
          disabled={submitting}
          onClick={() => void handleConfirm()}
          sx={{ textTransform: 'none' }}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ConfirmDeleteRoleModal
