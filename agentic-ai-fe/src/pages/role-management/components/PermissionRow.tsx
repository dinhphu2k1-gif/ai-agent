import { Box, IconButton, Typography } from '@mui/material'
import type { Permission } from '../types'
import PermissionChips from './PermissionChips'

interface PermissionRowProps {
  permission: Permission
  onEdit: () => void
  onDelete: () => void
}

const PermissionRow = ({ permission, onEdit, onDelete }: PermissionRowProps) => {
  const isDeny = permission.isHighlighted || permission.effect === 'DENY'

  return (
    <Box
      className="permission-row"
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 1,
        py: 1,
        px: 1,
        borderRadius: 1,
        ...(isDeny && {
          border: 1,
          borderColor: 'color-mix(in srgb, var(--mui-palette-errorContainer) 30%, transparent)',
          bgcolor: 'color-mix(in srgb, var(--mui-palette-errorContainer) 5%, transparent)',
        }),
        '&:hover': {
          bgcolor: isDeny
            ? 'color-mix(in srgb, var(--mui-palette-errorContainer) 8%, transparent)'
            : 'surfaceContainerLowest',
        },
        '&:hover .row-actions': { opacity: 1 },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          flex: 1,
          minWidth: 0,
          flexWrap: 'wrap',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.25,
            minWidth: 0,
          }}
        >
          {permission.path.map((segment, index) => (
            <Box key={`${segment.label}-${index}`} sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
              {index > 0 && (
                <span
                  className="material-symbols-outlined"
                  style={{
                    fontSize: 14,
                    color: 'var(--mui-palette-onSurfaceVariant)',
                  }}
                >
                  chevron_right
                </span>
              )}
              <Typography
                variant="labelMono"
                sx={{
                  fontSize: permission.path.length > 1 && index < permission.path.length - 1 ? 11 : 12,
                  color: index === permission.path.length - 1 ? 'onSurface' : 'onSurfaceVariant',
                }}
                noWrap
              >
                {segment.label}
              </Typography>
            </Box>
          ))}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
          <PermissionChips
            effect={permission.effect}
            action={permission.action}
            modifier={permission.modifier}
          />
        </Box>
      </Box>
      <Box
        className="row-actions"
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          opacity: 0,
          transition: 'opacity 0.15s ease',
          flexShrink: 0,
        }}
      >
        <IconButton
          size="small"
          aria-label="Edit permission"
          onClick={onEdit}
          sx={{
            color: 'onSurfaceVariant',
            '&:hover': { color: 'onSurface', bgcolor: 'surfaceVariant' },
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
            edit
          </span>
        </IconButton>
        <IconButton
          size="small"
          aria-label="Delete permission"
          onClick={onDelete}
          sx={{
            color: 'error.main',
            '&:hover': { color: 'error.main', bgcolor: 'errorContainer' },
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
            delete
          </span>
        </IconButton>
      </Box>
    </Box>
  )
}

export default PermissionRow
