import { useState } from 'react'
import { Box, Typography } from '@mui/material'
import { ResourceType } from '../types'
import type { ResourceNode } from '../types'

const TYPE_ICONS: Record<ResourceType, string> = {
  [ResourceType.Database]: 'database',
  [ResourceType.Schema]: 'folder',
  [ResourceType.Table]: 'table_view',
  [ResourceType.Column]: 'view_column',
}

const TYPE_ICON_COLORS: Record<ResourceType, string> = {
  [ResourceType.Database]: 'var(--mui-palette-secondary-main)',
  [ResourceType.Schema]: 'var(--mui-palette-tertiary)',
  [ResourceType.Table]: 'var(--mui-palette-onSurfaceVariant)',
  [ResourceType.Column]: 'var(--mui-palette-outline)',
}

interface ResourceTreeProps {
  resources: ResourceNode[]
  selectedId?: string | null
  onSelect?: (node: ResourceNode, path: ResourceNode[]) => void
}

const ResourceTree = ({ resources, selectedId, onSelect }: ResourceTreeProps) => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['db1', 'sch1']))
  const [collapseAll, setCollapseAll] = useState(false)

  const handleCollapseToggle = () => {
    if (collapseAll) {
      setExpanded(new Set(['db1', 'sch1']))
    } else {
      setExpanded(new Set())
    }
    setCollapseAll((prev) => !prev)
  }

  const toggleExpand = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const renderNode = (node: ResourceNode, path: ResourceNode[], depth: number) => {
    const hasChildren = !!(node.children && node.children.length > 0)
    const isExpanded = expanded.has(node.id)
    const isSelected = selectedId === node.id
    const currentPath = [...path, node]
    const icon = TYPE_ICONS[node.type]
    const iconColor = TYPE_ICON_COLORS[node.type]

    return (
      <Box key={node.id} sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
        <Box
          onClick={() => onSelect?.(node, currentPath)}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            pl: depth * 2 + 1,
            pr: 1,
            py: 0.75,
            borderRadius: 1,
            cursor: 'pointer',
            bgcolor: isSelected
              ? 'rgba(var(--mui-palette-secondary-mainChannel) / 0.1)'
              : 'transparent',
            border: isSelected ? 1 : 0,
            borderColor: 'rgba(var(--mui-palette-secondary-mainChannel) / 0.3)',
            color: isSelected ? 'secondary.light' : 'onSurface',
            '&:hover': {
              bgcolor: isSelected
                ? 'rgba(var(--mui-palette-secondary-mainChannel) / 0.1)'
                : 'surfaceContainerHighest',
            },
            transition: 'background-color 0.15s',
          }}
        >
          {/* Expand/Collapse chevron */}
          <Box
            component="span"
            onClick={hasChildren ? (e) => toggleExpand(node.id, e) : undefined}
            sx={{
              display: 'flex',
              alignItems: 'center',
              opacity: hasChildren ? 1 : 0,
              pointerEvents: hasChildren ? 'auto' : 'none',
              color: 'onSurfaceVariant',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
              {isExpanded ? 'expand_more' : 'chevron_right'}
            </span>
          </Box>

          {/* Icon */}
          <span
            className="material-symbols-outlined"
            style={{
              fontSize: node.type === ResourceType.Column ? 16 : 18,
              color: isSelected ? 'var(--mui-palette-secondary-fixed)' : iconColor,
            }}
          >
            {icon}
          </span>

          {/* Name */}
          <Typography
            variant="labelMono"
            sx={{
              flex: 1,
              color: isSelected ? 'var(--mui-palette-secondary-fixed)' : 'onSurfaceVariant',
              fontWeight: isSelected ? 'bold' : 'normal',
            }}
          >
            {node.name}
          </Typography>

          {/* Key icon for PK / FK columns */}
          {node.type === ResourceType.Column && node.isPrimaryKey && (
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 14, color: 'var(--mui-palette-warning-main)' }}
            >
              vpn_key
            </span>
          )}
          {node.type === ResourceType.Column && node.isForeignKey && (
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 14, color: 'var(--mui-palette-tertiary)' }}
            >
              vpn_key
            </span>
          )}

          {/* Check mark for selected row */}
          {isSelected && (
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 16, color: 'var(--mui-palette-secondary-fixed)' }}
            >
              check
            </span>
          )}
        </Box>

        {hasChildren && isExpanded && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
            {node.children!.map((child) => renderNode(child, currentPath, depth + 1))}
          </Box>
        )}
      </Box>
    )
  }

  return (
    <Box
      sx={{
        flex: 1,
        border: 1,
        borderColor: 'outlineVariant',
        borderRadius: 1,
        bgcolor: 'surfaceContainerLowest',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Tree Header */}
      <Box
        sx={{
          px: 2,
          py: 1.5,
          bgcolor: 'surfaceContainer',
          borderBottom: 1,
          borderColor: 'outlineVariant',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
          Data Catalog
        </Typography>
        <Box
          component="span"
          onClick={handleCollapseToggle}
          sx={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            color: 'onSurfaceVariant',
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
            {collapseAll ? 'unfold_more' : 'unfold_less'}
          </span>
        </Box>
      </Box>

      {/* Tree Nodes */}
      <Box
        sx={{
          p: 1,
          overflowY: 'auto',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 0.25,
        }}
      >
        {resources.map((node) => renderNode(node, [], 0))}
      </Box>
    </Box>
  )
}

export default ResourceTree
