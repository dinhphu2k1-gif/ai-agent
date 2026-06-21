import { Box, Grid, Skeleton, Stack, Typography } from '@mui/material'
import type { ResourceGroupViewModel, ResourceType, Role } from '../types'
import type { PermissionSummary } from '../types'
import PermissionsHeader from './PermissionsHeader'
import ResourceGroupSection from './ResourceGroupSection'
import PermissionsSummaryBar from './PermissionsSummaryBar'

interface PermissionsPanelProps {
  role: Role | null
  resourceGroups: ResourceGroupViewModel[]
  summary: PermissionSummary
  loading?: boolean
  expandedGroups: Record<ResourceType, boolean>
  onToggleGroup: (type: ResourceType) => void
  onAddPermission: () => void
  onEditPermission: (permissionId: string) => void
  onDeletePermission: (permissionId: string) => void
}

const PermissionsPanel = ({
  role,
  resourceGroups,
  summary,
  loading = false,
  expandedGroups,
  onToggleGroup,
  onAddPermission,
  onEditPermission,
  onDeletePermission,
}: PermissionsPanelProps) => {
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
      <PermissionsHeader role={role} onAddPermission={onAddPermission} />
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {!role ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
              Select a role to view permissions
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
              No permissions configured for this role
            </Typography>
          </Box>
        ) : (
          resourceGroups.map((group) => (
            <ResourceGroupSection
              key={group.type}
              group={group}
              expanded={expandedGroups[group.type]}
              onToggle={() => onToggleGroup(group.type)}
              onEditPermission={onEditPermission}
              onDeletePermission={onDeletePermission}
            />
          ))
        )}
      </Box>
      {role && <PermissionsSummaryBar summary={summary} />}
    </Grid>
  )
}

export default PermissionsPanel
