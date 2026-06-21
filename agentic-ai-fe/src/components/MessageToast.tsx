import { Alert, Snackbar } from '@mui/material'

import { useAppDispatch, useAppSelector } from '@/redux/hooks'
import { closeAlert, selectAlert } from '@/redux/reducers/AlertSlice'

const MessageToast = () => {
  const dispatch = useAppDispatch()
  const snackbar = useAppSelector(selectAlert)

  const handleClose = () => {
    dispatch(closeAlert())
  }

  return (
    <Snackbar
      open={Boolean(snackbar)}
      autoHideDuration={6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      {snackbar ? (
        <Alert
          onClose={handleClose}
          severity={snackbar.severity ?? 'info'}
          variant="filled"
          sx={{ width: '100%', maxWidth: 480 }}
        >
          {snackbar.children}
        </Alert>
      ) : undefined}
    </Snackbar>
  )
}

export default MessageToast
