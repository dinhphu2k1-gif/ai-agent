import { Box, Typography, Button } from '@mui/material'
import type { Role } from '../types'

interface PermissionsHeaderProps {
  role: Role | null
  onAddPermission: () => void
}

const PermissionsHeader = ({ role, onAddPermission }: PermissionsHeaderProps) => {
  return (
    <Box
      sx={{
        p: 2,
        borderBottom: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surface',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexShrink: 0,
        gap: 2,
      }}
    >
      <Box sx={{ minWidth: 0 }}>
        {role ? (
          <>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                '&:hover .edit-role-icon': { opacity: 1 },
              }}
            >
              <Typography variant="displaySm" sx={{ color: 'onSurface' }} noWrap>
                {role.name}
              </Typography>
              <span
                className="material-symbols-outlined edit-role-icon"
                style={{
                  fontSize: 18,
                  opacity: 0,
                  transition: 'opacity 0.15s ease',
                  color: 'var(--mui-palette-onSurfaceVariant)',
                }}
              >
                edit
              </span>
            </Box>
            <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', mt: 0.5 }}>
              Manage resource access policies for this role.
            </Typography>
          </>
        ) : (
          <Typography variant="displaySm" sx={{ color: 'onSurface' }}>
            Permissions
          </Typography>
        )}
      </Box>
      <Button
        size="small"
        disabled={!role}
        onClick={onAddPermission}
        startIcon={
          <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
            add
          </span>
        }
        sx={{
          flexShrink: 0,
          textTransform: 'none',
          fontWeight: 500,
          fontSize: 13,
          color: 'onSurface',
          bgcolor: 'surfaceContainer',
          border: 1,
          borderColor: 'outline',
          borderRadius: 1,
          px: 1.5,
          py: 0.75,
          '&:hover': { bgcolor: 'surfaceContainerHigh' },
        }}
      >
        Add Permission
      </Button>
    </Box>
  )
}

export default PermissionsHeader
