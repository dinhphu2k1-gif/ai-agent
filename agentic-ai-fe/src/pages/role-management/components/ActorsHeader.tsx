import { Box, Typography } from '@mui/material'

const ActorsHeader = () => {
  return (
    <Box
      sx={{
        p: 2,
        borderBottom: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surface',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
        Actors
      </Typography>
      <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', mt: 0.5 }}>
        Entities assigned to this role.
      </Typography>
    </Box>
  )
}

export default ActorsHeader
