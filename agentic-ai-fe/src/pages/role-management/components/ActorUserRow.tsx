import { Box, Typography, Avatar, IconButton } from '@mui/material'
import type { ActorUser } from '../types'

interface ActorUserRowProps {
  user: ActorUser
  onUnassign: () => void
}

const ActorUserRow = ({ user, onUnassign }: ActorUserRowProps) => {
  const initials = user.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        py: 0.75,
        px: 0.75,
        mx: -0.75,
        borderRadius: 1,
        '&:hover': { bgcolor: 'surfaceContainer' },
        '&:hover .unassign-btn': { opacity: 1 },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box sx={{ position: 'relative' }}>
          <Avatar
            src={user.avatarUrl}
            sx={{
              width: 32,
              height: 32,
              fontSize: 12,
              border: 1,
              borderColor: 'outlineVariant',
            }}
          >
            {initials}
          </Avatar>
          {user.isOnline && (
            <Box
              sx={{
                position: 'absolute',
                bottom: 0,
                right: 0,
                width: 10,
                height: 10,
                borderRadius: '50%',
                bgcolor: 'success.main',
                border: 2,
                borderColor: 'surface',
              }}
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Typography
            variant="bodyData"
            sx={{ color: 'onSurface', fontWeight: 500, lineHeight: 1.3 }}
            noWrap
          >
            {user.name}
          </Typography>
          <Typography
            variant="caption"
            sx={{ color: 'onSurfaceVariant', lineHeight: 1.3 }}
            noWrap
          >
            {user.email}
          </Typography>
        </Box>
      </Box>
      <IconButton
        className="unassign-btn"
        size="small"
        aria-label={`Unassign ${user.name}`}
        onClick={onUnassign}
        sx={{
          opacity: 0,
          color: 'onSurfaceVariant',
          transition: 'opacity 0.15s ease',
          '&:hover': { color: 'error.main' },
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
          close
        </span>
      </IconButton>
    </Box>
  )
}

export default ActorUserRow
