import { Box, Typography } from '@mui/material'

interface SqlQueryBlockProps {
  sql: string
}

const SqlQueryBlock = ({ sql }: SqlQueryBlockProps) => {
  if (!sql.trim()) return null

  return (
    <Box
      sx={{
        mb: 1.5,
        borderRadius: 1,
        border: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surfaceContainerLowest',
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          px: 1.5,
          py: 0.75,
          borderBottom: 1,
          borderColor: 'outlineVariant',
          bgcolor: 'surfaceContainerLow',
          display: 'flex',
          alignItems: 'center',
          gap: 0.75,
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 16, color: 'var(--mui-palette-onSurfaceVariant)' }}>
          code
        </span>
        <Typography variant="labelMono" sx={{ color: 'onSurfaceVariant' }}>
          SQL
        </Typography>
      </Box>
      <Box
        component="pre"
        sx={{
          m: 0,
          p: 1.5,
          overflowX: 'auto',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '12px',
          lineHeight: 1.5,
          color: 'onSurface',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {sql}
      </Box>
    </Box>
  )
}

export default SqlQueryBlock
