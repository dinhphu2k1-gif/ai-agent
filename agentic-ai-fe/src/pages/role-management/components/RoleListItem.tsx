import { Box, Typography, styled } from '@mui/material'
import type { Role } from '../types'
import RoleItemMenu from './RoleItemMenu'

const RoleCard = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'selected',
})<{ selected?: boolean }>(({ theme, selected }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  gap: theme.spacing(1.5),
  padding: theme.spacing(1.5),
  borderRadius: theme.shape.borderRadius * 2,
  borderLeft: '2px solid',
  borderLeftColor: selected ? 'var(--mui-palette-tertiary)' : 'transparent',
  backgroundColor: selected
    ? 'var(--mui-palette-surfaceContainerHigh)'
    : 'transparent',
  cursor: 'pointer',
  transition: 'background-color 0.15s ease',
  '&:hover': {
    backgroundColor: selected
      ? 'var(--mui-palette-surfaceContainerHighest)'
      : 'var(--mui-palette-surfaceContainer)',
  },
  '&:hover .role-item-menu': {
    opacity: 1,
  },
}))

interface RoleListItemProps {
  role: Role
  selected: boolean
  deleteDisabled?: boolean
  onSelect: () => void
  onRename: () => void
  onDelete: () => void
}

const RoleListItem = ({
  role,
  selected,
  deleteDisabled = false,
  onSelect,
  onRename,
  onDelete,
}: RoleListItemProps) => {
  const iconName = role.icon === 'shield_lock' ? 'shield_lock' : 'shield'

  return (
    <RoleCard selected={selected} onClick={onSelect} role="button" tabIndex={0}>
      <Box
        sx={{
          mt: 0.25,
          p: 0.75,
          borderRadius: '50%',
          bgcolor: 'roleViewerBg',
          color: 'roleViewerText',
          border: 1,
          borderColor: 'roleViewerBorder',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
          {iconName}
        </span>
      </Box>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Typography
            variant="bodyMain"
            sx={{ color: 'onSurface', fontWeight: 600 }}
            noWrap
          >
            {role.name}
          </Typography>
          <Box
            className="role-item-menu"
            onClick={(e) => e.stopPropagation()}
            sx={{ opacity: selected ? 1 : undefined, transition: 'opacity 0.15s ease', ml: 0.5 }}
          >
            <RoleItemMenu
              onRename={onRename}
              onDelete={onDelete}
              deleteDisabled={deleteDisabled}
            />
          </Box>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25, mt: 0.5 }}>
          <Typography
            variant="bodyData"
            sx={{ color: 'onSurfaceVariant', display: 'flex', alignItems: 'center', gap: 0.5 }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
              key
            </span>
            {role.permissionCount} permissions
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: 'onSurfaceVariant',
              opacity: 0.7,
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 12 }}>
              group
            </span>
            {role.userCount} users · {role.groupCount} groups
          </Typography>
        </Box>
      </Box>
    </RoleCard>
  )
}

export default RoleListItem
