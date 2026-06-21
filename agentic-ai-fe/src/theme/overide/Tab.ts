import type { Components } from '@mui/material'

export const MuiTab: Components['MuiTab'] = {
  defaultProps: {
    iconPosition: 'start',
  },
  styleOverrides: {
    root: {
      minHeight: 48,
    },
  },
}
