import { Box, Typography, Button } from '@mui/material'
import type { ActorUser } from '../types'
import ActorUserRow from './ActorUserRow'

interface ActorsUsersSectionProps {
  users: ActorUser[]
  visibleCount?: number
  assignDisabled?: boolean
  onAssign: () => void
  onUnassign: (userId: string) => void
  onShowMore?: () => void
}

const ActorsUsersSection = ({
  users,
  visibleCount = 2,
  assignDisabled = false,
  onAssign,
  onUnassign,
  onShowMore,
}: ActorsUsersSectionProps) => {
  const visible = users.slice(0, visibleCount)
  const hiddenCount = users.length - visibleCount

  return (
    <Box
      sx={{
        p: 2,
        borderBottom: 1,
        borderColor: 'color-mix(in srgb, var(--mui-palette-outlineVariant) 50%, transparent)',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 18, color: 'var(--mui-palette-primary-main)' }}
          >
            person
          </span>
          <Typography variant="bodyMain" sx={{ color: 'onSurface', fontWeight: 600 }}>
            Users
          </Typography>
          <Box
            sx={{
              px: 0.75,
              py: 0.25,
              borderRadius: 0.5,
              bgcolor: 'outlineVariant',
              color: 'outline',
              fontSize: 10,
              fontFamily: 'inherit',
              lineHeight: 1.4,
            }}
          >
            {users.length}
          </Box>
        </Box>
        <Button
          size="small"
          disabled={assignDisabled}
          onClick={onAssign}
          startIcon={
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
              add
            </span>
          }
          sx={{
            textTransform: 'none',
            fontWeight: 500,
            fontSize: 13,
            color: 'tertiary',
            minWidth: 'auto',
            px: 0.5,
            '&:hover': { color: 'tertiaryFixedDim', bgcolor: 'transparent' },
          }}
        >
          Assign
        </Button>
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {visible.map((user) => (
          <ActorUserRow key={user.id} user={user} onUnassign={() => onUnassign(user.id)} />
        ))}
        {hiddenCount > 0 && onShowMore && (
          <Box sx={{ textAlign: 'center', mt: 0.5 }}>
            <Button
              size="small"
              onClick={onShowMore}
              sx={{
                textTransform: 'none',
                fontSize: 12,
                color: 'onSurfaceVariant',
                fontWeight: 400,
                '&:hover': { color: 'onSurface', bgcolor: 'transparent' },
              }}
            >
              Show {hiddenCount} more...
            </Button>
          </Box>
        )}
      </Box>
    </Box>
  )
}

export default ActorsUsersSection
