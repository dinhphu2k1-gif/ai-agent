import type { AlertProps } from '@mui/material'
import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export interface AlertState {
  snackbar: Pick<AlertProps, 'children' | 'severity'> | null
}
const initialState: AlertState = {
  snackbar: null,
}
// create slice
export const alertSlice = createSlice({
  name: 'messageToast',
  initialState,
  reducers: {
    setAlert: (
      state: AlertState,
      action: PayloadAction<Pick<AlertProps, 'children' | 'severity'>>
    ) => {
      state.snackbar = action.payload
    },
    // close snackbar
    closeAlert: (state: AlertState) => {
      state.snackbar = null
    },
  },
  selectors: {
    selectAlert: (state) => state.snackbar,
  },
})
export const { setAlert, closeAlert } = alertSlice.actions
export const { selectAlert } = alertSlice.selectors
