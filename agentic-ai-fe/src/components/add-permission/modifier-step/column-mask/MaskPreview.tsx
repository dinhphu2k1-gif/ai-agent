import { Box, Typography } from '@mui/material'
import { MaskType } from '../../types'
import { renderMaskedValue } from './maskUtils'

interface MaskPreviewProps {
  maskType: MaskType
  maskPattern: string
}

const PREVIEW_SAMPLES = ['091-234-5678', '091-999-1234', '091-000-0000']

const MaskPreview = ({ maskType, maskPattern }: MaskPreviewProps) => {
  return (
    <Box>
      <Typography variant="headlineAgent" sx={{ fontSize: 13, color: 'onSurface', mb: 1 }}>
        Preview
      </Typography>
      <Box sx={{ border: 1, borderColor: 'outlineVariant', borderRadius: 2, overflow: 'hidden' }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            bgcolor: 'surfaceContainerHighest',
            borderBottom: 1,
            borderColor: 'outlineVariant',
            px: 1.5,
            py: 0.75,
          }}
        >
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
            Original (varchar)
          </Typography>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
            Masked Output
          </Typography>
        </Box>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            bgcolor: 'surfaceContainerLowest',
            fontFamily: 'var(--mui-fontFamily-label-mono)',
            fontSize: 12,
          }}
        >
          {PREVIEW_SAMPLES.map((sample, idx) => (
            <Box
              key={sample}
              sx={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                px: 1.5,
                py: 1,
                borderBottom: idx < PREVIEW_SAMPLES.length - 1 ? 1 : 0,
                borderColor: 'outlineVariant',
              }}
            >
              <Box component="span" sx={{ color: 'onSurfaceVariant' }}>
                {sample}
              </Box>
              <Box component="span">{renderMaskedValue(sample, maskType, maskPattern)}</Box>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  )
}

export default MaskPreview
