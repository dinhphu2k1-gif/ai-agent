import { Box, Typography, IconButton, Avatar } from '@mui/material'

const TopAppBar = () => {
  return (
    <Box
      component="header"
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        height: 48,
        px: 2,
        bgcolor: 'background.default',
        backdropFilter: 'blur(12px)',
        zIndex: 10,
        position: 'sticky',
        top: 0,
        flexShrink: 0,
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="headlineAgent" sx={{ fontWeight: 'bold', color: 'text.primary' }}>
          Analysis Workspace
        </Typography>
        <Typography variant="headlineAgent" sx={{ color: 'text.secondary', opacity: 0.5 }}>
          /
        </Typography>
        <Typography variant="headlineAgent" sx={{ color: 'primary.main' }}>
          Users
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <IconButton size="small" sx={{ color: 'text.secondary' }}>
          <span className="material-symbols-outlined">notifications</span>
        </IconButton>
        <Avatar
          sx={{
            width: 32,
            height: 32,
            border: 1,
            borderColor: 'divider',
          }}
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuDVZJHKU-gudBa_lSzH697szrnDUV7ttCxjr-s94hrjTIr90tfbGcodnyvA4doqBS94LYKvR9qtqr6B1nZphO9Z6Fr08Aqi2f9zSu9jRKztS4Uq2EgdlteGerqIZhkIG5xqOACO2uaqk2jizrT5DReEUCdb_9RxW0XK55-XKqfdwr0_Vs44eRwWt25flEIr6SvSoPv_ETtJ9gDbCQMdXFOEUvFT2WsDh8glRhz4s9dIzykUFTtUYUIvmDBCKEKOmTRJ_5yVqOAG37lT"
        />
      </Box>
    </Box>
  )
}

export default TopAppBar
