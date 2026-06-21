import { Box, TextField, InputAdornment, Typography } from '@mui/material'
import ResourceTree from './ResourceTree'
import SelectedResourceInfo from './SelectedResourceInfo'
import type { ResourceNode } from '../types'

interface ResourceStepProps {
  selectedPath: ResourceNode[] | null
  roleName: string
  resources: ResourceNode[]
  readOnly?: boolean
  onSelect: (node: ResourceNode, path: ResourceNode[]) => void
  onClear: () => void
}

const ResourceStep = ({
  selectedPath,
  roleName,
  resources,
  readOnly = false,
  onSelect,
  onClear,
}: ResourceStepProps) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        flex: 1,
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {readOnly && (
        <Box
          sx={{
            px: 1.5,
            py: 1,
            borderRadius: 1,
            bgcolor: 'surfaceContainerLow',
            border: 1,
            borderColor: 'outlineVariant',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 1,
            flexShrink: 0,
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 18, color: 'var(--mui-palette-onSurfaceVariant)' }}
          >
            lock
          </span>
          <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', lineHeight: 1.4 }}>
            Resource is locked while editing. Continue to update actions, effect, and modifiers.
          </Typography>
        </Box>
      )}

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          flex: 1,
          overflow: 'hidden',
          opacity: readOnly ? 0.5 : 1,
          pointerEvents: readOnly ? 'none' : 'auto',
          userSelect: readOnly ? 'none' : 'auto',
          filter: readOnly ? 'grayscale(0.15)' : 'none',
          transition: 'opacity 0.2s ease',
        }}
        aria-disabled={readOnly}
      >
      {/* Search Input */}
      <TextField
        disabled={readOnly}
        placeholder="Search databases, tables, columns..."
        fullWidth
        variant="outlined"
        sx={{
          '& .MuiOutlinedInput-root': {
            bgcolor: 'surfaceContainer',
            borderRadius: 1,
            color: 'onSurface',
            py: 0.5,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'primary.main',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: 'primary.main',
            },
          },
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: 'outlineVariant',
          },
        }}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: 20, color: 'var(--mui-palette-onSurfaceVariant)' }}
                >
                  search
                </span>
              </InputAdornment>
            ),
          },
        }}
      />

      {/* Resource Tree with Data Catalog header */}
      <ResourceTree
        resources={resources}
        selectedId={selectedPath ? selectedPath[selectedPath.length - 1].id : null}
        readOnly={readOnly}
        onSelect={onSelect}
      />

      {/* Breadcrumb + Warning */}
      <SelectedResourceInfo
        selectedPath={selectedPath}
        roleName={roleName}
        readOnly={readOnly}
        onClear={onClear}
      />
      </Box>
    </Box>
  )
}

export default ResourceStep
