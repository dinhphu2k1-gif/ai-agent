import { Box, Grid, Typography } from '@mui/material'
import type { GroupMember, GroupRoleAssignment, InheritedSummary, UserGroup } from '../types'
import GroupDetailHeader from './GroupDetailHeader'
import MembersSection from './MembersSection'
import RolesSection from './RolesSection'
import GroupImpactBanner from './GroupImpactBanner'

interface GroupDetailPanelProps {
  group: UserGroup | null
  members: GroupMember[]
  roles: GroupRoleAssignment[]
  inheritedSummary: InheritedSummary
  detailLoading?: boolean
  onDeleteGroup: () => void
  onAddMember: () => void
  onRemoveMember: (memberId: string) => void
  onAssignRoles: () => void
  onRemoveRole: (roleId: string) => void
}

const GroupDetailPanel = ({
  group,
  members,
  roles,
  inheritedSummary,
  detailLoading,
  onDeleteGroup,
  onAddMember,
  onRemoveMember,
  onAssignRoles,
  onRemoveRole,
}: GroupDetailPanelProps) => {
  return (
    <Grid
      size={{ xs: 12, md: 8, lg: 6 }}
      sx={{
        bgcolor: 'surfaceDim',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        borderBottom: { xs: 1, md: 1, lg: 0 },
        borderRight: { lg: 1 },
        borderColor: 'var(--mui-palette-outlineVariant) !important',
      }}
    >
      <GroupDetailHeader group={group} onDeleteGroup={onDeleteGroup} />
      <Box sx={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        {!group ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
              Select a group to view members and roles
            </Typography>
          </Box>
        ) : (
          <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <MembersSection
              members={members}
              loading={detailLoading}
              assignDisabled={!group || Boolean(detailLoading)}
              onAddMember={onAddMember}
              onRemoveMember={onRemoveMember}
            />
            <RolesSection
              roles={roles}
              inheritedSummary={inheritedSummary}
              loading={detailLoading}
              assignDisabled={!group || Boolean(detailLoading)}
              onAssignRoles={onAssignRoles}
              onRemoveRole={onRemoveRole}
            />
          </Box>
        )}
      </Box>
      {group && <GroupImpactBanner memberCount={group.memberCount} />}
    </Grid>
  )
}

export default GroupDetailPanel
