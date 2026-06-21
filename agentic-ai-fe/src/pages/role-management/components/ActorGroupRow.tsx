import { Box, Typography, IconButton } from '@mui/material'
import type { ActorGroup } from '../types'

interface ActorGroupRowProps {
  group: ActorGroup
  onUnassign: () => void
}

const ActorGroupRow = ({ group, onUnassign }: ActorGroupRowProps) => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        py: 1,
        px: 1,
        mx: -1,
        borderRadius: 1,
        '&:hover': { bgcolor: 'surfaceContainer' },
        '&:hover .unassign-btn': { opacity: 1 },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: 1,
            bgcolor: 'statusActiveBg',
            color: 'statusActiveText',
            border: 1,
            borderColor: 'statusActiveBorder',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
            group
          </span>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Typography
            variant="bodyData"
            sx={{ color: 'onSurface', fontWeight: 500, lineHeight: 1.3 }}
            noWrap
          >
            {group.name}
          </Typography>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant', lineHeight: 1.3 }}>
            {group.memberCount} members
          </Typography>
        </Box>
      </Box>
      <IconButton
        className="unassign-btn"
        size="small"
        aria-label={`Unassign ${group.name}`}
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

export default ActorGroupRow
