import { Box, Typography } from '@mui/material'

interface ActorsImpactBannerProps {
  totalAffectedUsers: number
}

const ActorsImpactBanner = ({ totalAffectedUsers }: ActorsImpactBannerProps) => {
  return (
    <Box
      sx={{
        p: 2,
        mt: 'auto',
        flexShrink: 0,
        borderTop: 1,
        borderColor: 'color-mix(in srgb, var(--mui-palette-tertiary) 20%, transparent)',
        bgcolor: 'color-mix(in srgb, var(--mui-palette-tertiary) 10%, transparent)',
        display: 'flex',
        gap: 1,
        alignItems: 'flex-start',
      }}
    >
      <span
        className="material-symbols-outlined"
        style={{ fontSize: 20, color: 'var(--mui-palette-tertiary)', flexShrink: 0 }}
      >
        info
      </span>
      <Typography variant="bodyData" sx={{ color: 'tertiary', lineHeight: 1.4 }}>
        This role currently affects{' '}
        <Box component="strong" sx={{ fontWeight: 700, color: 'onSurfaceVariant' }}>
          {totalAffectedUsers} users total
        </Box>{' '}
        (direct + via groups).
      </Typography>
    </Box>
  )
}

export default ActorsImpactBanner
