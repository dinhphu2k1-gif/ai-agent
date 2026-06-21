import { Box, Typography, Collapse } from '@mui/material'
import type { EffectivePermission, EffectiveResourceGroupViewModel, ResourceType } from '../types'
import EffectivePermissionRow from './EffectivePermissionRow'

interface ResourceGroupSectionProps {
  group: EffectiveResourceGroupViewModel
  expanded: boolean
  onToggle: () => void
  onEditPermission: (permission: EffectivePermission) => void
  onDeletePermission: (permission: EffectivePermission) => void
}

const typeLabel: Record<ResourceType, string> = {
  DATABASE: 'DATABASE',
  SCHEMA: 'SCHEMA',
  TABLE: 'TABLE',
  COLUMN: 'COLUMN',
}

const ResourceGroupSection = ({
  group,
  expanded,
  onToggle,
  onEditPermission,
  onDeletePermission,
}: ResourceGroupSectionProps) => {
  return (
    <Box
      sx={{
        border: 1,
        borderColor: 'outlineVariant',
        borderRadius: 2,
        bgcolor: 'surface',
        overflow: 'auto',
      }}
    >
      <Box
        component="button"
        type="button"
        aria-expanded={expanded}
        onClick={onToggle}
        sx={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
          p: 1.5,
          border: 'none',
          borderBottom: expanded ? 1 : 0,
          borderColor: 'outlineVariant',
          bgcolor: 'surfaceContainerLowest',
          cursor: 'pointer',
          textAlign: 'left',
          '&:hover': { bgcolor: 'surfaceContainer' },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 18, color: 'var(--mui-palette-tertiary)' }}
          >
            {group.icon}
          </span>
          <Typography variant="labelMono" sx={{ color: 'onSurface' }}>
            {typeLabel[group.type]}
          </Typography>
          <Box
            sx={{
              px: 0.75,
              py: 0.25,
              borderRadius: 0.5,
              bgcolor: 'surfaceVariant',
              color: 'onSurfaceVariant',
              fontSize: 10,
              fontFamily: 'JetBrains Mono, monospace',
              fontWeight: 500,
              ml: 0.5,
            }}
          >
            {group.count}
          </Box>
        </Box>
        <span
          className="material-symbols-outlined"
          style={{ fontSize: 20, color: 'var(--mui-palette-onSurfaceVariant)' }}
        >
          {expanded ? 'expand_less' : 'expand_more'}
        </span>
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ p: 1, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {group.permissions.map((perm) => (
            <EffectivePermissionRow
              key={perm.id}
              permission={perm}
              onEdit={() => onEditPermission(perm)}
              onDelete={() => onDeletePermission(perm)}
            />
          ))}
        </Box>
      </Collapse>
    </Box>
  )
}

export default ResourceGroupSection
