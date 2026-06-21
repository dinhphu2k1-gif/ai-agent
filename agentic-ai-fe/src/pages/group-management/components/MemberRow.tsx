import { Box, Typography, Avatar, IconButton } from '@mui/material'
import type { GroupMember } from '../types'

interface MemberRowProps {
  member: GroupMember
  avatarVariant?: 'primary' | 'secondary'
  onRemove: () => void
}

const MemberRow = ({ member, avatarVariant = 'primary', onRemove }: MemberRowProps) => {
  const isActive = member.status === 'Active'

  return (
    <Box
      className="member-row"
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        py: 1,
        px: 2,
        borderBottom: 1,
        borderColor: 'color-mix(in srgb, var(--mui-palette-outlineVariant) 50%, transparent)',
        transition: 'background-color 0.15s ease',
        '&:last-of-type': { borderBottom: 0 },
        '&:hover': { bgcolor: 'surfaceBright' },
        '&:hover .remove-btn': { opacity: 1 },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 0 }}>
        <Avatar
          src={member.avatarUrl}
          sx={{
            width: 32,
            height: 32,
            fontSize: 14,
            fontWeight: 600,
            fontFamily: 'Inter, sans-serif',
            bgcolor: avatarVariant === 'primary' ? 'primaryContainer' : 'secondaryContainer',
            color:
              avatarVariant === 'primary' ? 'onPrimaryContainer' : 'onSecondaryContainer',
          }}
        >
          {member.initials}
        </Avatar>
        <Box sx={{ minWidth: 0, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography
              variant="headlineAgent"
              sx={{ color: 'onSurface', fontSize: 14, lineHeight: 1.3 }}
              noWrap
            >
              {member.name}
            </Typography>
            <Box
              component="span"
              title={member.status}
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                flexShrink: 0,
                bgcolor: isActive ? 'success.main' : 'onSurfaceVariant',
                opacity: isActive ? 1 : 0.45,
              }}
            />
          </Box>
          <Typography
            variant="bodyData"
            sx={{ color: 'onSurfaceVariant', fontSize: 12, lineHeight: 1.3 }}
            noWrap
          >
            {member.email}
          </Typography>
        </Box>
      </Box>
      <IconButton
        className="remove-btn"
        size="small"
        aria-label={`Remove ${member.name}`}
        onClick={onRemove}
        sx={{
          opacity: 0,
          p: 0.5,
          color: 'onSurfaceVariant',
          transition: 'opacity 0.15s ease, color 0.15s ease',
          flexShrink: 0,
          '&:hover': { color: 'error.main', bgcolor: 'transparent' },
        }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
          person_remove
        </span>
      </IconButton>
    </Box>
  )
}

export default MemberRow
