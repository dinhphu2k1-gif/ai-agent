import { Box, Typography } from '@mui/material'
import { MaskType } from '../../types'

interface MaskTypeSelectorProps {
  maskType: MaskType
  onChangeMaskType: (type: MaskType) => void
}

const MASK_CONFIGS = [
  {
    type: MaskType.Full,
    label: 'FULL',
    preview: '"0912345" → "***"',
    dotColor: 'var(--mui-palette-error-main)',
    selectedBorderColor: 'var(--mui-palette-error-main)',
    selectedBgColor: 'var(--mui-palette-errorContainer)',
  },
  {
    type: MaskType.Partial,
    label: 'PARTIAL',
    preview: '"0912345" → "091***"',
    dotColor: 'var(--mui-palette-tertiary)',
    selectedBorderColor: 'var(--mui-palette-tertiary)',
    selectedBgColor: 'var(--mui-palette-tertiaryContainer)',
    hasAccentBar: true,
  },
  {
    type: MaskType.Hash,
    label: 'HASH',
    preview: '"091" → "e3b0c..."',
    dotColor: 'var(--mui-palette-secondary-main)',
    selectedBorderColor: 'var(--mui-palette-secondary-main)',
    selectedBgColor: 'var(--mui-palette-secondaryContainer)',
  },
  {
    type: MaskType.Nullify,
    label: 'NULLIFY',
    preview: '"0912" → NULL',
    dotColor: 'var(--mui-palette-outline)',
    selectedBorderColor: 'var(--mui-palette-outline)',
    selectedBgColor: 'var(--mui-palette-surfaceContainerLow)',
  },
]

const MaskTypeSelector = ({ maskType, onChangeMaskType }: MaskTypeSelectorProps) => {
  return (
    <Box>
      <Typography variant="caption" sx={{ color: 'onSurfaceVariant', display: 'block', mb: 1 }}>
        Mask Type
      </Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.5 }}>
        {MASK_CONFIGS.map((config) => {
          const isSelected = maskType === config.type
          return (
            <Box
              key={config.type}
              onClick={() => onChangeMaskType(config.type)}
              sx={{
                position: 'relative',
                p: 1.5,
                borderRadius: 2,
                border: 1,
                borderColor: isSelected ? config.selectedBorderColor : 'outlineVariant',
                bgcolor: isSelected ? config.selectedBgColor : 'surfaceContainerLowest',
                cursor: 'pointer',
                '&:hover': { borderColor: 'outline' },
                transition: 'all 0.2s',
                overflow: 'hidden',
              }}
            >
              {isSelected && config.hasAccentBar && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    bottom: 0,
                    width: 8,
                    bgcolor: config.selectedBorderColor,
                  }}
                />
              )}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: config.dotColor,
                  }}
                />
                <Typography
                  variant="headlineAgent"
                  sx={{
                    fontSize: 13,
                    color: isSelected && config.hasAccentBar ? config.dotColor : 'onSurface',
                    fontWeight: isSelected && config.hasAccentBar ? 'bold' : 'normal',
                  }}
                >
                  {config.label}
                </Typography>
              </Box>
              <Typography
                variant="caption"
                sx={{
                  fontSize: 10,
                  color: 'onSurfaceVariant',
                  fontFamily: 'var(--mui-fontFamily-label-mono)',
                }}
              >
                {config.preview}
              </Typography>
            </Box>
          )
        })}
      </Box>
    </Box>
  )
}

export default MaskTypeSelector
