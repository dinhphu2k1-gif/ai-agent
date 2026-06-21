import { Box, Typography } from '@mui/material'
import { ResourceType, PermissionEffect, MaskType } from '../../types'
import type { ResourceNode } from '../../types'

interface ReviewStepProps {
  roleName: string
  selectedPath: ResourceNode[] | null
  selectedActions: string[]
  effect: PermissionEffect
  rowFilterEnabled: boolean
  conditionExpression: string
  columnMaskEnabled: boolean
  maskType: MaskType
  maskPattern: string
}

const ReviewStep = ({
  roleName,
  selectedPath,
  selectedActions,
  effect,
  rowFilterEnabled,
  conditionExpression,
  columnMaskEnabled,
  maskType,
  maskPattern,
}: ReviewStepProps) => {
  if (!selectedPath || selectedPath.length === 0) return null

  const targetNode = selectedPath[selectedPath.length - 1]
  const isColumn = targetNode.type === ResourceType.Column
  const fullPathString = selectedPath.map((node) => node.name).join(' / ')

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Review Summary Card */}
      <Box
        sx={{
          p: 2,
          borderRadius: 1,
          bgcolor: 'surfaceContainerLow',
          border: 1,
          borderColor: 'outlineVariant',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
          Review Summary
        </Typography>

        {/* Resource Row */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
            Resource
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 18, color: 'var(--mui-palette-onSurfaceVariant)' }}
            >
              {isColumn ? 'view_column' : 'table_view'}
            </span>
            <Typography variant="labelMono" sx={{ color: 'onSurface', wordBreak: 'break-all' }}>
              {fullPathString}
            </Typography>
            <Box
              sx={{
                px: 1,
                py: 0.25,
                bgcolor: 'surfaceContainerHighest',
                color: 'onSurfaceVariant',
                border: 1,
                borderColor: 'outlineVariant',
                borderRadius: 0.5,
              }}
            >
              <Typography variant="labelMono" sx={{ fontSize: 10, fontWeight: 'bold' }}>
                {targetNode.type.toUpperCase()}
              </Typography>
            </Box>
            {isColumn && (
              <Box
                sx={{
                  px: 1,
                  py: 0.25,
                  bgcolor: 'surfaceContainerLowest',
                  border: 1,
                  borderColor: 'outlineVariant',
                  borderRadius: 0.5,
                }}
              >
                <Typography variant="labelMono" sx={{ fontSize: 10, color: 'onSurfaceVariant' }}>
                  varchar
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Actions Row */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
            Actions
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            {selectedActions.map((act) => (
              <Box
                key={act}
                sx={{
                  px: 1,
                  py: 0.5,
                  bgcolor: 'secondaryContainer',
                  color: 'onSecondaryContainer',
                  border: 1,
                  borderColor: 'outlineVariant',
                  borderRadius: 0.5,
                }}
              >
                <Typography variant="labelMono" sx={{ fontSize: 11, fontWeight: 'bold' }}>
                  {act}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>

        {/* Effect Row */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, alignItems: 'start' }}>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
            Effect
          </Typography>
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.5,
              px: 1.25,
              py: 0.5,
              bgcolor: effect === PermissionEffect.Allow ? 'statusActiveBg' : 'errorContainer',
              color: effect === PermissionEffect.Allow ? 'success.main' : 'error.main',
              border: 1,
              borderColor: effect === PermissionEffect.Allow ? 'statusActiveBorder' : 'error.main',
              borderRadius: 0.5,
            }}
          >
            {effect === PermissionEffect.Allow && (
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 14, color: 'var(--mui-palette-success-main)' }}
              >
                check_circle
              </span>
            )}
            <Typography variant="labelMono" sx={{ fontSize: 11, fontWeight: 'bold' }}>
              {effect}
            </Typography>
          </Box>
        </Box>

        {/* Modifier Row */}
        {isColumn
          ? columnMaskEnabled && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
                  Column mask
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      px: 1,
                      py: 0.5,
                      bgcolor: 'tertiaryContainer',
                      color: 'onTertiaryContainer',
                      border: 1,
                      borderColor: 'outlineVariant',
                      borderRadius: 0.5,
                    }}
                  >
                    <Typography variant="labelMono" sx={{ fontSize: 11, fontWeight: 'bold' }}>
                      {maskType}
                    </Typography>
                  </Box>
                  {maskType === MaskType.Partial && (
                    <Box
                      sx={{
                        px: 1,
                        py: 0.5,
                        bgcolor: 'surface',
                        border: 1,
                        borderColor: 'outlineVariant',
                        borderRadius: 0.5,
                      }}
                    >
                      <Typography variant="labelMono" sx={{ fontSize: 11 }}>
                        {maskPattern}
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Box>
            )
          : rowFilterEnabled && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
                  Row filter
                </Typography>
                <Box
                  sx={{
                    p: 1.25,
                    bgcolor: 'surfaceContainerLowest',
                    border: 1,
                    borderColor: 'outlineVariant',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="labelMono" sx={{ color: 'onSurface' }}>
                    <Box component="span" sx={{ color: 'primary.main' }}>
                      {conditionExpression || "region = 'North'"}
                    </Box>
                  </Typography>
                </Box>
              </Box>
            )}
      </Box>

      {/* Impact Preview */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Typography
          variant="caption"
          sx={{ color: 'onSurfaceVariant', fontWeight: 'bold', textTransform: 'uppercase' }}
        >
          Impact Preview
        </Typography>
        <Box
          sx={{
            p: 1.5,
            bgcolor: 'surfaceContainerHigh',
            border: 1,
            borderColor: 'outlineVariant',
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'tertiary.main' }}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
              group
            </span>
            <Typography variant="headlineAgent" sx={{ fontWeight: 'bold' }}>
              {roleName}
            </Typography>
          </Box>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 18, color: 'var(--mui-palette-onSurfaceVariant)' }}
          >
            arrow_forward
          </span>
          <Typography variant="caption" sx={{ color: 'onSurface' }}>
            {isColumn ? (
              <>
                <strong>17 users</strong> total (5 direct + 12 via 2 groups) will see{' '}
                <code>phone_number</code> masked.
              </>
            ) : (
              <>
                Role: <strong>{roleName}</strong> → 5 direct + 12 via 2 groups ={' '}
                <Box component="span" sx={{ color: 'primary.main', fontWeight: 'bold' }}>
                  17 users affected
                </Box>
              </>
            )}
          </Typography>
        </Box>
      </Box>
    </Box>
  )
}

export default ReviewStep
