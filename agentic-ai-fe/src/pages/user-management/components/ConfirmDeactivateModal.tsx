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

interface ConfirmDeactivateModalProps {
  open: boolean
  onClose: () => void
  selectedCount: number
  submitting?: boolean
  onConfirm: () => void | Promise<void>
}

const ConfirmDeactivateModal = ({
  open,
  onClose,
  selectedCount,
  submitting = false,
  onConfirm,
}: ConfirmDeactivateModalProps) => {
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
      {/* Header */}
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
          Vô hiệu hóa tài khoản
        </Typography>
        <IconButton
          onClick={onClose}
          size="small"
          sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            close
          </span>
        </IconButton>
      </DialogTitle>

      {/* Body */}
      <DialogContent sx={{ p: 2, bgcolor: 'var(--mui-palette-surfaceContainer)' }}>
        <Stack spacing={2} sx={{ pt: 2 }}>
          <Typography variant="bodyMain" sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}>
            Bạn có chắc chắn muốn vô hiệu hóa{' '}
            <Box component="span" sx={{ color: 'var(--mui-palette-onSurface)', fontWeight: 600 }}>
              {selectedCount} tài khoản
            </Box>{' '}
            đã chọn? Hành động này sẽ thu hồi ngay lập tức quyền truy cập vào tất cả tài nguyên dữ
            liệu và kênh tác vụ.
          </Typography>

          <Box
            sx={{
              p: 1.5,
              bgcolor: 'var(--mui-palette-surfaceContainerLowest)',
              borderRadius: 1,
              border: 1,
              borderColor: 'var(--mui-palette-outlineVariant)',
              display: 'flex',
              gap: 1.5,
              alignItems: 'flex-start',
            }}
          >
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 18, color: 'var(--mui-palette-onSurfaceVariant)', marginTop: 2 }}
            >
              info
            </span>
            <Typography variant="caption" sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}>
              Hành động này có thể được hoàn tác sau này bởi quản trị viên hệ thống.
            </Typography>
          </Box>
        </Stack>
      </DialogContent>

      {/* Footer */}
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
          variant="outlined"
          sx={{
            color: 'var(--mui-palette-onSurfaceVariant)',
            textTransform: 'none',
            fontWeight: 600,
            borderColor: 'var(--mui-palette-outlineVariant)',
          }}
        >
          Hủy
        </Button>
        <Button
          variant="contained"
          onClick={() => void handleConfirm()}
          disabled={submitting}
          color="error"
          startIcon={
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 16, fontVariationSettings: "'FILL' 1" }}
            >
              person_off
            </span>
          }
          sx={{
            textTransform: 'none',
            fontWeight: 600,
          }}
        >
          Vô hiệu hóa
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ConfirmDeactivateModal
