import { Box, Typography, Button } from '@mui/material'
import type { UserGroup } from '../types'

interface GroupPermissionsHeaderProps {
  group: UserGroup | null
  roleCount: number
  addDisabled?: boolean
  onAddPermission: () => void
}

const GroupPermissionsHeader = ({
  group,
  roleCount,
  addDisabled: addDisabledProp,
  onAddPermission,
}: GroupPermissionsHeaderProps) => {
  const addDisabled = addDisabledProp ?? !group

  return (
    <Box
      sx={{
        p: 2,
        borderBottom: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surface',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: 2,
      }}
    >
      <Box sx={{ minWidth: 0 , display: 'flex', flexDirection: 'column'}}>
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
          Effective Permissions
        </Typography>
        <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', mt: 0.5 }}>
          {roleCount > 0
            ? `Direct group grants plus permissions inherited from ${roleCount} assigned role${roleCount === 1 ? '' : 's'}.`
            : 'Add permissions directly to this group, or assign roles to inherit their permissions.'}
        </Typography>
      </Box>
      <Button
        size="small"
        disabled={addDisabled}
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

export default GroupPermissionsHeader
