import { Box, CircularProgress } from '@mui/material'

export default function Loading(): React.ReactNode {
  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <CircularProgress />
    </Box>
  )
}
