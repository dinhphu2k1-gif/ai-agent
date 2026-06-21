import { Box, Grid, Skeleton, Stack } from '@mui/material'
import type { Role } from '../types'
import RoleListHeader from './RoleListHeader'
import RoleListItem from './RoleListItem'

interface RoleListPanelProps {
  roles: Role[]
  selectedRoleId: string | null
  searchQuery: string
  loading?: boolean
  onSearchChange: (value: string) => void
  onSelectRole: (roleId: string) => void
  onAddRole: () => void
  onRenameRole: (roleId: string) => void
  onDeleteRole: (roleId: string) => void
  canDeleteRoles?: boolean
}

const RoleListPanel = ({
  roles,
  selectedRoleId,
  searchQuery,
  loading = false,
  onSearchChange,
  onSelectRole,
  onAddRole,
  onRenameRole,
  onDeleteRole,
  canDeleteRoles = true,
}: RoleListPanelProps) => {
  return (
    <Grid
      size={{ xs: 12, md: 4, lg: 3 }}
      sx={{
        overflow: 'hidden',
        bgcolor: 'surface',
        display: 'flex',
        flexDirection: 'column',
        borderBottom: { xs: 1, md: 1, lg: 0 },
        borderRight: { md: 1, lg: 1 },
        borderColor: 'var(--mui-palette-outlineVariant) !important',
      }}
    >
      <RoleListHeader
        searchQuery={searchQuery}
        onSearchChange={onSearchChange}
        onAddRole={onAddRole}
      />
      <Box sx={{ flex: 1, overflowY: 'auto', p: 1 }}>
        <Stack spacing={0.5}>
          {loading && roles.length === 0
            ? [1, 2, 3].map((key) => (
                <Skeleton
                  key={key}
                  variant="rounded"
                  height={72}
                  sx={{ bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}
                />
              ))
            : null}
          {roles.map((role) => (
            <RoleListItem
              key={role.id}
              role={role}
              selected={role.id === selectedRoleId}
              onSelect={() => onSelectRole(role.id)}
              onRename={() => onRenameRole(role.id)}
              deleteDisabled={!canDeleteRoles}
              onDelete={() => onDeleteRole(role.id)}
            />
            ))}
        </Stack>
      </Box>
    </Grid>
  )
}

export default RoleListPanel
