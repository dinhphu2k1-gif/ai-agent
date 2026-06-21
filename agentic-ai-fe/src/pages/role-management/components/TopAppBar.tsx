import { Box, Typography, IconButton, Breadcrumbs, Link } from '@mui/material'

const TopAppBar = () => {
  return (
    <Box
      component="header"
      sx={{
        height: 56,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: 2,
        borderBottom: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surfaceContainerLow',
      }}
    >
      <Box>
        <Breadcrumbs
          aria-label="breadcrumb"
          sx={{
            mb: 0.25,
            '& .MuiBreadcrumbs-separator': { mx: 0.5, color: 'onSurfaceVariant' },
          }}
        >
          <Link
            underline="hover"
            color="inherit"
            href="#"
            variant="caption"
            sx={{ color: 'onSurfaceVariant', fontSize: 11 }}
          >
            Admin
          </Link>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant', fontSize: 11 }}>
            Roles
          </Typography>
        </Breadcrumbs>
        <Typography variant="displaySm" sx={{ color: 'onSurface', lineHeight: 1.2 }}>
          Role Management
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <IconButton size="small" aria-label="Search">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            search
          </span>
        </IconButton>
        <IconButton size="small" aria-label="Notifications">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            notifications
          </span>
        </IconButton>
        <IconButton size="small" aria-label="Help">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            help
          </span>
        </IconButton>
      </Box>
    </Box>
  )
}

export default TopAppBar
