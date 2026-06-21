import { Box, Typography, IconButton } from '@mui/material'
import type { ResourceNode } from '../types'

interface SelectedResourceInfoProps {
  selectedPath: ResourceNode[] | null
  roleName: string
  readOnly?: boolean
  onClear: () => void
}

const SelectedResourceInfo = ({ selectedPath, readOnly = false, onClear }: SelectedResourceInfoProps) => {
  if (!selectedPath || selectedPath.length === 0) return null

  const targetNode = selectedPath[selectedPath.length - 1]

  return (
    <>
      {/* Selected Breadcrumb Pill */}
      <Box
        sx={{
          p: 1.5,
          bgcolor: 'surfaceContainerHigh',
          border: 1,
          borderColor: 'outlineVariant',
          borderRadius: 1,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            flexWrap: 'wrap',
            fontFamily: 'var(--mui-fontFamily-label-mono)',
          }}
        >
          {selectedPath.map((node, index) => {
            const isLast = index === selectedPath.length - 1
            const textColor =
              index === 0
                ? 'var(--mui-palette-secondary-main)'
                : !isLast
                  ? 'var(--mui-palette-tertiary)'
                  : 'var(--mui-palette-secondary-fixed)'

            return (
              <Box key={node.id} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {index > 0 && (
                  <Typography variant="labelMono" sx={{ color: 'onSurfaceVariant' }}>
                    /
                  </Typography>
                )}
                <Typography
                  variant="labelMono"
                  sx={{ color: textColor, fontWeight: isLast ? 'bold' : 'normal' }}
                >
                  {node.name}
                </Typography>
              </Box>
            )
          })}

          <Box
            sx={{
              ml: 1,
              px: 0.75,
              py: 0.25,
              bgcolor: 'surfaceContainerHighest',
              border: 1,
              borderColor: 'outlineVariant',
              borderRadius: 0.5,
            }}
          >
            <Typography variant="labelMono" sx={{ fontSize: 10, color: 'onSurfaceVariant' }}>
              {targetNode.type.toUpperCase()}
            </Typography>
          </Box>
        </Box>

        {!readOnly && (
          <IconButton
            size="small"
            sx={{ color: 'onSurfaceVariant', '&:hover': { color: 'onSurface' } }}
            onClick={onClear}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
              close
            </span>
          </IconButton>
        )}
      </Box>

      {/* Warning Callout — amber / ochre theme matching design */}
      {/* {showWarning && (
        <Box
          sx={{
            p: 1.5,
            bgcolor: '#422006',
            border: 1,
            borderColor: '#78350f',
            borderRadius: 1,
            display: 'flex',
            gap: 1.5,
            alignItems: 'flex-start',
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{
              color: '#fbbf24',
              fontVariationSettings: "'FILL' 1",
              fontSize: 20,
              marginTop: 2,
            }}
          >
            warning
          </span>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <Typography variant="headlineAgent" sx={{ color: '#fde68a' }}>
              Existing Permissions
            </Typography>
            <Typography variant="bodyData" sx={{ color: '#fcd34d' }}>
              Role &apos;{roleName}&apos; already has implicitly inherited permissions on this{' '}
              {targetNode.type} via the parent schema.
            </Typography>
          </Box>
        </Box>
      )} */}
    </>
  )
}

export default SelectedResourceInfo
