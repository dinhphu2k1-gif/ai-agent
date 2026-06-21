import { Box, Grid, Skeleton, Stack, Typography } from '@mui/material'
import type { ActorGroup, ActorUser, Role } from '../types'
import ActorsHeader from './ActorsHeader'
import ActorsUsersSection from './ActorsUsersSection'
import ActorsGroupsSection from './ActorsGroupsSection'
import ActorsImpactBanner from './ActorsImpactBanner'

interface ActorsPanelProps {
  role: Role | null
  users: ActorUser[]
  groups: ActorGroup[]
  totalAffectedUsers: number
  loading?: boolean
  showAllUsers: boolean
  onAssignUsers: () => void
  onAssignGroups: () => void
  onUnassignUser: (userId: string) => void
  onUnassignGroup: (groupId: string) => void
  onShowMoreUsers: () => void
}

const ActorsPanel = ({
  role,
  users,
  groups,
  totalAffectedUsers,
  loading,
  showAllUsers,
  onAssignUsers,
  onAssignGroups,
  onUnassignUser,
  onUnassignGroup,
  onShowMoreUsers,
}: ActorsPanelProps) => {
  const visibleCount = showAllUsers ? users.length : 2

  return (
    <Grid
      size={{ xs: 12, md: 12, lg: 3 }}
      sx={{
        height: { lg: '100%' },
        overflow: 'hidden',
        bgcolor: 'surface',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <ActorsHeader />
      <Box sx={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        {!role ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
              Select a role to view actors
            </Typography>
          </Box>
        ) : loading ? (
          <Stack spacing={1.5} sx={{ p: 2 }}>
            {[1, 2, 3, 4].map((key) => (
              <Skeleton
                key={key}
                variant="rounded"
                height={48}
                sx={{ bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}
              />
            ))}
          </Stack>
        ) : (
          <>
            <ActorsUsersSection
              users={users}
              visibleCount={visibleCount}
              assignDisabled={!role}
              onAssign={onAssignUsers}
              onUnassign={onUnassignUser}
              onShowMore={showAllUsers ? undefined : onShowMoreUsers}
            />
            <ActorsGroupsSection
              groups={groups}
              assignDisabled={!role}
              onAssign={onAssignGroups}
              onUnassign={onUnassignGroup}
            />
          </>
        )}
      </Box>
      {role && <ActorsImpactBanner totalAffectedUsers={totalAffectedUsers} />}
    </Grid>
  )
}

export default ActorsPanel
