import { Box, Typography, Button, Skeleton, Stack } from '@mui/material'
import type { GroupRoleAssignment, InheritedSummary } from '../types'
import GroupRoleCard from './GroupRoleCard'
import InheritedPermissionsSummary from './InheritedPermissionsSummary'

interface RolesSectionProps {
  roles: GroupRoleAssignment[]
  inheritedSummary: InheritedSummary
  loading?: boolean
  assignDisabled: boolean
  onAssignRoles: () => void
  onRemoveRole: (roleId: string) => void
  onViewRolePermissions?: (roleId: string) => void
}

const RolesSection = ({
  roles,
  inheritedSummary,
  loading = false,
  assignDisabled,
  onAssignRoles,
  onRemoveRole,
  onViewRolePermissions,
}: RolesSectionProps) => {
  return (
    <Box
      sx={{
        border: 1,
        borderColor: 'outlineVariant',
        borderRadius: 3,
        bgcolor: 'surfaceContainer',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'outlineVariant',
          bgcolor: 'surfaceContainerHigh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
            Roles
          </Typography>
          <Box
            sx={{
              px: 1,
              py: 0.25,
              borderRadius: 999,
              bgcolor: 'color-mix(in srgb, var(--mui-palette-tertiaryContainer) 50%, transparent)',
              color: 'tertiary.main',
            }}
          >
            <Typography variant="labelMono" component="span" sx={{ fontSize: 12 }}>
              {roles.length}
            </Typography>
          </Box>
        </Box>
        <Button
          size="small"
          disabled={assignDisabled}
          onClick={onAssignRoles}
          startIcon={
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
              add_moderator
            </span>
          }
          sx={{
            textTransform: 'none',
            fontFamily: 'JetBrains Mono, monospace',
            fontWeight: 500,
            fontSize: 12,
            color: 'onSurface',
            bgcolor: 'transparent',
            border: 1,
            borderColor: 'outlineVariant',
            borderRadius: 2,
            px: 1.25,
            py: 0.5,
            minWidth: 0,
            boxShadow: 'none',
            '&:hover': { bgcolor: 'surfaceBright', boxShadow: 'none' },
          }}
        >
          Assign role
        </Button>
      </Box>

      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
        {loading ? (
          <Stack spacing={1}>
            {[1, 2].map((key) => (
              <Skeleton
                key={key}
                variant="rounded"
                height={88}
                sx={{ bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}
              />
            ))}
          </Stack>
        ) : roles.length === 0 ? (
          <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', py: 2, textAlign: 'center' }}>
            No roles assigned to this group
          </Typography>
        ) : (
          roles.map((role) => (
            <GroupRoleCard
              key={role.id}
              role={role}
              onRemove={() => onRemoveRole(role.id)}
              onViewPermissions={
                onViewRolePermissions ? () => onViewRolePermissions(role.id) : undefined
              }
            />
          ))
        )}
      </Box>

      {!loading && roles.length > 0 && (
        <InheritedPermissionsSummary summary={inheritedSummary} />
      )}
    </Box>
  )
}

export default RolesSection
