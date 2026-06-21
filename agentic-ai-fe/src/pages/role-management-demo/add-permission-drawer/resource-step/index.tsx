import { Box, TextField, InputAdornment } from '@mui/material'
import ResourceTree from './ResourceTree'
import SelectedResourceInfo from './SelectedResourceInfo'
import type { ResourceNode } from '../../types'

interface ResourceStepProps {
  selectedPath: ResourceNode[] | null
  roleName: string
  onSelect: (node: ResourceNode, path: ResourceNode[]) => void
  onClear: () => void
}

const ResourceStep = ({ selectedPath, roleName, onSelect, onClear }: ResourceStepProps) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1, overflow: 'hidden' }}>
      {/* Search Input */}
      <TextField
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
        selectedId={selectedPath ? selectedPath[selectedPath.length - 1].id : null}
        onSelect={onSelect}
      />

      {/* Breadcrumb + Warning */}
      <SelectedResourceInfo selectedPath={selectedPath} roleName={roleName} onClear={onClear} />
    </Box>
  )
}

export default ResourceStep
