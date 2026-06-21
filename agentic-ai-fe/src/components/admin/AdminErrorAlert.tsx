import { Alert, Button } from '@mui/material'
import type { SxProps, Theme } from '@mui/material/styles'

interface AdminErrorAlertProps {
  message: string
  onRetry?: () => void
  sx?: SxProps<Theme>
}

const AdminErrorAlert = ({ message, onRetry, sx }: AdminErrorAlertProps) => (
  <Alert
    severity="error"
    variant="outlined"
    action={
      onRetry ? (
        <Button color="inherit" size="small" onClick={onRetry}>
          Retry
        </Button>
      ) : undefined
    }
    sx={{ borderColor: 'outlineVariant', flexShrink: 0, ...sx }}
  >
    {message}
  </Alert>
)

export default AdminErrorAlert
