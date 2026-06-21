import { Box, Typography } from '@mui/material'
import { ResourceType } from '../types'
import type { ResourceNode } from '../types'
import { TYPE_ICONS } from '../constants'

interface ContextBarProps {
  selectedPath: ResourceNode[]
  resourceType: ResourceType | null
  targetNode: ResourceNode | null
}

const ContextBar = ({ selectedPath, resourceType, targetNode }: ContextBarProps) => {
  const typeConfig = resourceType ? TYPE_ICONS[resourceType] : null
  let leafIcon = typeConfig?.icon || 'info'
  let leafIconColor = typeConfig?.color || 'var(--mui-palette-onSurfaceVariant)'

  if (resourceType === ResourceType.Column) {
    if (targetNode?.isPrimaryKey) {
      leafIcon = 'key'
      leafIconColor = 'var(--mui-palette-warning-main)'
    } else if (targetNode?.isForeignKey) {
      leafIcon = 'key'
      leafIconColor = 'var(--mui-palette-tertiary)'
    }
  }

  return (
    <Box
      sx={{
        px: 3,
        py: 1.5,
        bgcolor: 'surfaceContainerHigh',
        borderBottom: 1,
        borderColor: 'outlineVariant',
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
      }}
    >
      {selectedPath.length > 1 && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'onSurfaceVariant' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
            {selectedPath[0].type === ResourceType.Database ? 'database' : 'folder'}
          </span>
          <Typography variant="caption" sx={{ color: 'inherit' }}>
            {selectedPath
              .slice(0, -1)
              .map((n) => n.name)
              .join(' / ')}
          </Typography>
        </Box>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 18, color: leafIconColor }}
          >
            {leafIcon}
          </span>
          <Typography variant="labelMono" sx={{ fontWeight: 'bold', color: 'onSurface' }}>
            {resourceType === ResourceType.Column && selectedPath.length >= 2
              ? `${selectedPath[selectedPath.length - 2].name}.${targetNode?.name}`
              : targetNode?.name}
          </Typography>
        </Box>
        <Box
          sx={{
            px: 1,
            py: 0.25,
            borderRadius: 0.5,
            bgcolor: 'surfaceContainerLowest',
            border: 1,
            borderColor: 'outlineVariant',
            color: 'onSurfaceVariant',
            fontFamily: 'var(--mui-fontFamily-label-mono)',
            fontSize: 10,
            textTransform: 'lowercase',
          }}
        >
          {resourceType === ResourceType.Column ? 'varchar' : resourceType}
        </Box>
      </Box>
    </Box>
  )
}

export default ContextBar
