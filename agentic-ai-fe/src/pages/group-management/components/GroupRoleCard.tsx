import { Box, Typography, IconButton, Button } from '@mui/material'
import type { GroupRoleAssignment } from '../types'

interface GroupRoleCardProps {
  role: GroupRoleAssignment
  onRemove: () => void
  onViewPermissions?: () => void
}

const GroupRoleCard = ({ role, onRemove, onViewPermissions }: GroupRoleCardProps) => {
  return (
    <Box
      className="role-card"
      sx={{
        p: 1.5,
        borderRadius: 2,
        border: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surface',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: 1,
        transition: 'border-color 0.15s ease',
        '&:hover': { borderColor: 'tertiary.main' },
        '&:hover .remove-role-btn': { opacity: 1 },
      }}
    >
      <Box sx={{ display: 'flex', gap: 1.5, minWidth: 0, flex: 1 }}>
        <Box sx={{ mt: 0.25, color: 'tertiary.main', flexShrink: 0, lineHeight: 0 }}>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 20, fontVariationSettings: "'FILL' 1" }}
          >
            shield
          </span>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0 }}>
          <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
            {role.name}
          </Typography>
          <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }}>
            {role.description}
          </Typography>
          <Button
            size="small"
            disabled={!onViewPermissions}
            onClick={onViewPermissions}
            sx={{
              alignSelf: 'flex-start',
              mt: 0.5,
              p: 0,
              minWidth: 0,
              textTransform: 'none',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 12,
              fontWeight: 500,
              color: 'primary.main',
              gap: 0.5,
              '&:hover': { bgcolor: 'transparent', opacity: 0.85 },
              '&.Mui-disabled': { color: 'primary.main', opacity: 0.5 },
            }}
            endIcon={
              <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                open_in_new
              </span>
            }
          >
            View permissions
          </Button>
        </Box>
      </Box>
      <IconButton
        className="remove-role-btn"
        size="small"
        aria-label={`Remove role ${role.name}`}
        onClick={onRemove}
        sx={{
          opacity: 0,
          p: 0.5,
          color: 'onSurfaceVariant',
          transition: 'opacity 0.15s ease, color 0.15s ease',
          flexShrink: 0,
          '&:hover': { color: 'error.main', bgcolor: 'transparent' },
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
          remove_circle_outline
        </span>
      </IconButton>
    </Box>
  )
}

export default GroupRoleCard
