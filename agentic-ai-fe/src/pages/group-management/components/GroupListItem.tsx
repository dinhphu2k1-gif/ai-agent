import { Box, Typography, styled } from '@mui/material'
import type { UserGroup } from '../types'

const GroupCard = styled(Box, {
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
}))

interface GroupListItemProps {
  group: UserGroup
  selected: boolean
  onSelect: () => void
}

const GroupListItem = ({ group, selected, onSelect }: GroupListItemProps) => {
  return (
    <GroupCard
      selected={selected}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect()
        }
      }}
    >
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
          groups
        </span>
      </Box>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="bodyMain" sx={{ color: 'onSurface', fontWeight: 600 }} noWrap>
          {group.name}
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25, mt: 0.5 }}>
          <Typography
            variant="bodyData"
            sx={{ color: 'onSurfaceVariant', display: 'flex', alignItems: 'center', gap: 0.5 }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
              person
            </span>
            {group.memberCount} members
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
              shield
            </span>
            {group.roleCount} roles
          </Typography>
        </Box>
      </Box>
    </GroupCard>
  )
}

export default GroupListItem
