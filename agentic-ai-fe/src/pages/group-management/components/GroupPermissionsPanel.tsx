import { Box, Grid, Skeleton, Stack, Typography } from '@mui/material'
import PermissionsSummaryBar from '@/pages/role-management/components/PermissionsSummaryBar'
import type {
  EffectivePermission,
  EffectiveResourceGroupViewModel,
  PermissionSummary,
  ResourceType,
  UserGroup,
} from '../types'
import GroupPermissionsHeader from './GroupPermissionsHeader'
import ResourceGroupSection from './ResourceGroupSection'

interface GroupPermissionsPanelProps {
  group: UserGroup | null
  roleCount: number
  resourceGroups: EffectiveResourceGroupViewModel[]
  summary: PermissionSummary
  loading?: boolean
  expandedGroups: Record<ResourceType, boolean>
  onToggleGroup: (type: ResourceType) => void
  onAddPermission: () => void
  onEditPermission: (permission: EffectivePermission) => void
  onDeletePermission: (permission: EffectivePermission) => void
}

const GroupPermissionsPanel = ({
  group,
  roleCount,
  resourceGroups,
  summary,
  loading = false,
  expandedGroups,
  onToggleGroup,
  onAddPermission,
  onEditPermission,
  onDeletePermission,
}: GroupPermissionsPanelProps) => {
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
      <GroupPermissionsHeader
        group={group}
        roleCount={roleCount}
        addDisabled={!group || loading}
        onAddPermission={onAddPermission}
      />
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          minHeight: 0,
        }}
      >
        {!group ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
              Select a group to view effective permissions
            </Typography>
          </Box>
        ) : loading ? (
          <Stack spacing={2}>
            {[1, 2, 3].map((key) => (
              <Skeleton
                key={key}
                variant="rounded"
                height={72}
                sx={{ bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}
              />
            ))}
          </Stack>
        ) : resourceGroups.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
              No permissions yet. Use Add Permission to grant access directly on this group.
            </Typography>
          </Box>
        ) : (
          resourceGroups.map((resourceGroup) => (
            <ResourceGroupSection
              key={resourceGroup.type}
              group={resourceGroup}
              expanded={expandedGroups[resourceGroup.type]}
              onToggle={() => onToggleGroup(resourceGroup.type)}
              onEditPermission={onEditPermission}
              onDeletePermission={onDeletePermission}
            />
          ))
        )}
      </Box>
      {group && resourceGroups.length > 0 && <PermissionsSummaryBar summary={summary} />}
    </Grid>
  )
}

export default GroupPermissionsPanel
