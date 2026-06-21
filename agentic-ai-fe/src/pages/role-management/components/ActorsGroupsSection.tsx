import { Box, Typography, Button } from '@mui/material'
import type { ActorGroup } from '../types'
import ActorGroupRow from './ActorGroupRow'

interface ActorsGroupsSectionProps {
  groups: ActorGroup[]
  assignDisabled?: boolean
  onAssign: () => void
  onUnassign: (groupId: string) => void
}

const ActorsGroupsSection = ({
  groups,
  assignDisabled = false,
  onAssign,
  onUnassign,
}: ActorsGroupsSectionProps) => {
  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 18, color: 'var(--mui-palette-statusActiveText)' }}
          >
            group_work
          </span>
          <Typography variant="bodyMain" sx={{ color: 'onSurface', fontWeight: 600 }}>
            Groups
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
              fontWeight: 600,
              lineHeight: 1.4,
            }}
          >
            {groups.length}
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
        {groups.map((group) => (
          <ActorGroupRow key={group.id} group={group} onUnassign={() => onUnassign(group.id)} />
        ))}
      </Box>
    </Box>
  )
}

export default ActorsGroupsSection
