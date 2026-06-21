import { Box, Typography } from '@mui/material'

const ActorPanel = () => {
  return (
    <Box
      sx={{
        flex: 1,
        bgcolor: 'surfaceContainerLow',
        p: 3,
        display: { xs: 'none', lg: 'block' },
      }}
    >
      <Typography variant="headlineAgent" sx={{ color: 'onSurface', mb: 2 }}>
        Assigned Users
      </Typography>
    </Box>
  )
}

export default ActorPanel
