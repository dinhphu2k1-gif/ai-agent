import type { Components } from '@mui/material'

export const MuiSelect: Components['MuiSelect'] = {
  defaultProps: {
    variant: 'outlined',
    size: 'small',
    sx: {
      bgcolor: 'var(--mui-palette-surfaceContainer)',
    }
  },
  styleOverrides: {},
}
