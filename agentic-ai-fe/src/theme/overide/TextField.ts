import type { Components } from '@mui/material'

export const MuiTextField: Components['MuiTextField'] = {
  defaultProps: {
    variant: 'outlined',
    size: 'small',
    fullWidth: true,
    sx: {
      '& .MuiOutlinedInput-root': {
        bgcolor: 'var(--mui-palette-surfaceContainer)',
      },
    }
  },
  styleOverrides: {},
}
