import {
  Avatar,
  Box,
  Typography,
  Stack,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import { useTheme } from '@mui/material/styles'
import {
  IconDotsVertical,
  IconSun,
  IconMoon,
  IconDeviceDesktop,
  IconLogout,
} from '@tabler/icons-react'
import { useState } from 'react'

import { useAppDispatch, useAppSelector } from '@/redux/hooks'
import { selectThemeMode, setThemeMode, type ThemeMode } from '@/redux/reducers/theme'

interface UserProfileProps {
  drawerOpen?: boolean
}

const UserProfile = ({ drawerOpen = true }: UserProfileProps) => {
  const theme = useTheme()
  const dispatch = useAppDispatch()
  const mode = useAppSelector(selectThemeMode)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleThemeChange = (newMode: ThemeMode) => {
    dispatch(setThemeMode(newMode))
    handleMenuClose()
  }

  if (!drawerOpen) {
    return (
      <Box
        sx={{
          p: 1.5,
          borderTop: `1px solid ${theme.vars.palette.outlineVariant}`,
          bgcolor: theme.vars.palette.surfaceContainerLow,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <Avatar
          src="/assets/images/users/user-round.svg" // Placeholder or fallback
          sx={{
            width: 36,
            height: 36,
            bgcolor: theme.vars.palette.primary.main,
            fontSize: '14px',
            fontWeight: 600,
          }}
        >
          AR
        </Avatar>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        p: 2,
        borderTop: `1px solid ${theme.vars.palette.outlineVariant}`,
        bgcolor: theme.vars.palette.surfaceContainerLow,
      }}
    >
      <Stack
        direction="row"
        spacing={1.5}
        sx={{ alignItems: 'center', justifyContent: 'space-between' }}
      >
        <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', overflow: 'hidden' }}>
          <Avatar
            src="/assets/images/users/user-round.svg" // Placeholder or fallback
            sx={{
              width: 36,
              height: 36,
              bgcolor: theme.vars.palette.primary.main,
              fontSize: '14px',
              fontWeight: 600,
            }}
          >
            AR
          </Avatar>
          <Box sx={{ overflow: 'hidden' }}>
            <Typography
              variant="bodyMain"
              sx={{
                display: 'block',
                fontWeight: 600,
                color: theme.vars.palette.onSurface,
                whiteSpace: 'nowrap',
                textOverflow: 'ellipsis',
                overflow: 'hidden',
              }}
            >
              Alex Rivera
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: theme.vars.palette.onSurfaceVariant,
                display: 'block',
              }}
            >
              System Admin
            </Typography>
          </Box>
        </Stack>
        <IconButton
          size="small"
          sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}
          onClick={handleMenuOpen}
        >
          <IconDotsVertical size={18} />
        </IconButton>
      </Stack>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'top' }}
        slotProps={{
          paper: {
            sx: {
              mt: -1,
              bgcolor: 'var(--mui-palette-surfaceContainerHigh)',
              backgroundImage: 'none',
              border: `1px solid var(--mui-palette-outlineVariant)`,
              boxShadow: '0px 8px 24px rgba(0,0,0,0.15)', // Tonal layering shadow
              minWidth: 180,
              '& .MuiMenuItem-root': {
                color: 'var(--mui-palette-onSurface)',
                '&:hover': {
                  bgcolor: 'var(--mui-palette-surfaceContainerHighest)',
                },
                '&.Mui-selected': {
                  bgcolor: 'var(--mui-palette-surfaceContainerHighest)',
                  color: 'var(--mui-palette-primary-main)',
                  '& .MuiListItemIcon-root': {
                    color: 'var(--mui-palette-primary-main)',
                  },
                },
              },
              '& .MuiListItemIcon-root': {
                color: 'var(--mui-palette-onSurfaceVariant)',
                minWidth: 32,
              },
            },
          },
        }}
      >
        <MenuItem onClick={() => handleThemeChange('light')} selected={mode === 'light'}>
          <ListItemIcon>
            <IconSun size={18} />
          </ListItemIcon>
          <ListItemText
            primary="Light Mode"
            slotProps={{
              primary: { variant: 'bodyMain' },
            }}
          />
        </MenuItem>
        <MenuItem onClick={() => handleThemeChange('dark')} selected={mode === 'dark'}>
          <ListItemIcon>
            <IconMoon size={18} />
          </ListItemIcon>
          <ListItemText
            primary="Dark Mode"
            slotProps={{
              primary: { variant: 'bodyMain' },
            }}
          />
        </MenuItem>
        <MenuItem onClick={() => handleThemeChange('system')} selected={mode === 'system'}>
          <ListItemIcon>
            <IconDeviceDesktop size={18} />
          </ListItemIcon>
          <ListItemText
            primary="System Mode"
            slotProps={{
              primary: { variant: 'bodyMain' },
            }}
          />
        </MenuItem>
        <Divider sx={{ my: 0.5, borderColor: 'var(--mui-palette-outlineVariant)' }} />
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <IconLogout size={18} />
          </ListItemIcon>
          <ListItemText
            primary="Logout"
            slotProps={{
              primary: { variant: 'bodyMain' },
            }}
          />
        </MenuItem>
      </Menu>
    </Box>
  )
}

export default UserProfile
