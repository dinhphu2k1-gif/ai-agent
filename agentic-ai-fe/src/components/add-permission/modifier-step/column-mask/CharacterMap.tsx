import { Box, Typography } from '@mui/material'

interface CharacterMapProps {
  maskPattern: string
}

const CharacterMap = ({ maskPattern }: CharacterMapProps) => {
  return (
    <Box
      sx={{
        bgcolor: 'surfaceContainer',
        p: 1.5,
        borderRadius: 2,
        border: 1,
        borderColor: 'outlineVariant',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
          Character Mapping
        </Typography>
        <Typography variant="labelMono" sx={{ fontSize: 10, color: 'onSurfaceVariant' }}>
          Len: {maskPattern.length}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', gap: '2px', overflowX: 'auto', pb: 1 }}>
        {maskPattern.split('').map((char, idx) => {
          const isMasked = char === 'X' || char === 'x'
          return (
            <Box
              key={idx}
              sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 24 }}
            >
              <Typography
                variant="labelMono"
                sx={{ fontSize: 10, color: isMasked ? 'error.main' : 'secondary.main' }}
              >
                {char}
              </Typography>
              <Box
                sx={{
                  width: '100%',
                  height: 4,
                  bgcolor: isMasked ? 'error.main' : 'secondary.main',
                  borderRadius: '2px',
                  my: 0.5,
                }}
              />
              <Typography
                variant="labelMono"
                sx={{ fontSize: 10, color: isMasked ? 'error.main' : 'onSurface' }}
              >
                {isMasked ? '*' : char}
              </Typography>
            </Box>
          )
        })}
      </Box>
    </Box>
  )
}

export default CharacterMap
