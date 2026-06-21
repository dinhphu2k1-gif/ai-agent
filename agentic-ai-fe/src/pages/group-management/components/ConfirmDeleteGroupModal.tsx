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

interface ConfirmDeleteGroupModalProps {
  open: boolean
  groupName: string
  submitting?: boolean
  onClose: () => void
  onConfirm: () => void | Promise<void>
}

const ConfirmDeleteGroupModal = ({
  open,
  groupName,
  submitting = false,
  onClose,
  onConfirm,
}: ConfirmDeleteGroupModalProps) => {
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
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
            warning
          </span>
        </Box>
        <Typography variant="headlineAgent" sx={{ flex: 1 }}>
          Delete group
        </Typography>
        <IconButton onClick={onClose} size="small" sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            close
          </span>
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 2, bgcolor: 'var(--mui-palette-surfaceContainer)' }}>
        <Stack spacing={2} sx={{ pt: 2 }}>
          <Typography variant="bodyMain" sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}>
            Are you sure you want to delete{' '}
            <Box component="span" sx={{ color: 'var(--mui-palette-onSurface)', fontWeight: 600 }}>
              {groupName}
            </Box>
            ? Members will lose group-based access from assigned roles.
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
        <Button
          onClick={onClose}
          disabled={submitting}
          variant="outlined"
          sx={{
            color: 'var(--mui-palette-onSurfaceVariant)',
            textTransform: 'none',
            fontWeight: 600,
            borderColor: 'var(--mui-palette-outlineVariant)',
          }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          color="error"
          disabled={submitting}
          onClick={() => void handleConfirm()}
          sx={{ textTransform: 'none', fontWeight: 600 }}
        >
          Delete group
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ConfirmDeleteGroupModal
