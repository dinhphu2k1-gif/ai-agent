import { Box, Typography, Button, TextField } from '@mui/material'

interface PatternInputProps {
  maskPattern: string
  onChangeMaskPattern: (pattern: string) => void
}

const QUICK_FILLS = [
  { label: 'Phone VN', pattern: '091-XXX-XXXX' },
  { label: 'Credit card', pattern: 'XXXX-XXXX-XXXX-1234' },
  { label: 'Email local', pattern: 'XXXXX@gmail.com' },
]

const PatternInput = ({ maskPattern, onChangeMaskPattern }: PatternInputProps) => {
  return (
    <Box
      sx={{
        p: 2,
        border: 1,
        borderColor: 'var(--mui-palette-tertiary)',
        borderRadius: 2,
        bgcolor: 'surfaceContainerLowest',
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="labelMono" sx={{ fontWeight: 'bold', color: 'onSurface' }}>
          mask_pattern
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            color: 'var(--mui-palette-tertiary)',
            fontSize: 10,
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 12 }}>
            info
          </span>
          Pattern length maps to string
        </Box>
      </Box>

      <TextField
        size="small"
        value={maskPattern}
        onChange={(e) => onChangeMaskPattern(e.target.value)}
        fullWidth
        sx={{
          '& .MuiOutlinedInput-root': {
            bgcolor: 'surface',
            borderRadius: 1,
            fontFamily: 'var(--mui-fontFamily-label-mono)',
            color: 'onSurface',
          },
        }}
      />

      <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
        Legend:{' '}
        <Box
          component="span"
          sx={{ color: 'error.main', fontFamily: 'var(--mui-fontFamily-label-mono)' }}
        >
          X
        </Box>{' '}
        → masked (*),{' '}
        <Box
          component="span"
          sx={{ color: 'secondary.main', fontFamily: 'var(--mui-fontFamily-label-mono)' }}
        >
          other
        </Box>{' '}
        → revealed
      </Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
        {QUICK_FILLS.map(({ label, pattern }) => {
          const isActive = maskPattern === pattern
          return (
            <Button
              key={pattern}
              size="small"
              onClick={() => onChangeMaskPattern(pattern)}
              sx={{
                px: 1.5,
                py: 0.5,
                borderRadius: 1,
                bgcolor: isActive ? 'tertiaryContainer' : 'surfaceContainer',
                color: isActive ? 'var(--mui-palette-tertiary)' : 'onSurfaceVariant',
                border: 1,
                borderColor: isActive ? 'var(--mui-palette-tertiary)' : 'outlineVariant',
                textTransform: 'none',
                fontSize: 12,
              }}
            >
              {label}
            </Button>
          )
        })}
      </Box>
    </Box>
  )
}

export default PatternInput
