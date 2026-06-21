import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox,
  Avatar,
  Box,
  Typography,
  Chip,
  IconButton,
  Skeleton,
  styled,
} from '@mui/material'

const StatusChip = styled(Chip)(({ theme, color }) => ({
  fontWeight: 'bold',
  fontSize: '10px',
  height: 24,
  px: 0,
  ...(color === 'success' && {
    backgroundColor: 'var(--mui-palette-statusActiveBg)',
    color: 'var(--mui-palette-statusActiveText)',
    border: '1px solid var(--mui-palette-statusActiveBorder)',
  }),
  ...(color === 'default' && {
    backgroundColor: theme.palette.surfaceContainer,
    color: theme.palette.onSurfaceVariant,
    border: `1px solid ${theme.palette.outlineVariant}`,
  }),
}))

const GroupChip = styled(Chip)(({ theme }) => ({
  fontSize: '10px',
  height: 20,
  borderRadius: theme.shape.borderRadius,
  fontFamily: 'JetBrains Mono',
  backgroundColor: 'var(--mui-palette-groupBg)',
  color: 'var(--mui-palette-tertiary)',
  border: '1px solid var(--mui-palette-tertiaryContainer)',
}))

const RoleChip = styled(Chip)<{ label?: string }>(({ theme, label }) => {
  const isSecondaryRole = label === 'Viewer' || label === 'Editor' || label === 'Deployer'
  return {
    fontSize: '10px',
    height: 20,
    borderRadius: theme.shape.borderRadius,
    fontFamily: 'JetBrains Mono',
    backgroundColor: isSecondaryRole
      ? 'var(--mui-palette-roleViewerBg)'
      : 'var(--mui-palette-roleAdminBg)',
    color: isSecondaryRole
      ? 'var(--mui-palette-roleViewerText)'
      : 'var(--mui-palette-primaryFixed)',
    border: `1px solid ${isSecondaryRole ? 'var(--mui-palette-roleViewerBorder)' : 'var(--mui-palette-primaryContainer)'}`,
  }
})

export interface UserNamedRef {
  id: string
  name: string
}

export interface User {
  id: string
  name: string
  email: string
  status: 'Active' | 'Inactive'
  groups: string[]
  roles: string[]
  groupRefs?: UserNamedRef[]
  roleRefs?: UserNamedRef[]
  lastActive: string
  initials: string
}

interface UserTableProps {
  users: User[]
  usersLoading?: boolean
  selectedIds: string[]
  onSelectAll: (event: React.ChangeEvent<HTMLInputElement>) => void
  onSelectOne: (id: string) => void
  onRowClick: (user: User) => void
}

const UserTable = ({
  users,
  usersLoading = false,
  selectedIds,
  onSelectAll,
  onSelectOne,
  onRowClick,
}: UserTableProps) => {
  return (
    <TableContainer
      sx={{
        flex: 1,
        overflow: 'auto',
        borderRadius: 2,
        border: 1,
        borderColor: 'outlineVariant',
        '&::-webkit-scrollbar': { width: 6, height: 6 },
        '&::-webkit-scrollbar-thumb': { bgcolor: 'transparent', borderRadius: 10 },
        '&:hover::-webkit-scrollbar-thumb': { bgcolor: 'surfaceVariant' },
      }}
    >
      <Table
        stickyHeader
        aria-label="user table"
        sx={{ minWidth: 800, '& .MuiTableCell-root': { py: 1.5, px: 1.5 } }}
      >
        <TableHead>
          <TableRow>
            <TableCell
              padding="checkbox"
              sx={{
                bgcolor: 'surfaceContainerLow',
                borderBottom: 1,
                borderColor: 'outlineVariant',
                py: '5px !important',
              }}
            >
              <Checkbox
                indeterminate={selectedIds.length > 0 && selectedIds.length < users.length}
                checked={users.length > 0 && selectedIds.length === users.length}
                onChange={onSelectAll}
                size="small"
              />
            </TableCell>
            <TableCell
              sx={{
                bgcolor: 'surfaceContainerLow',
                borderBottom: 1,
                borderColor: 'outlineVariant',
                typography: 'labelMono',
                color: 'onSurfaceVariant',
                textTransform: 'uppercase',
              }}
            >
              User
            </TableCell>
            <TableCell
              sx={{
                bgcolor: 'surfaceContainerLow',
                borderBottom: 1,
                borderColor: 'outlineVariant',
                typography: 'labelMono',
                color: 'onSurfaceVariant',
                textTransform: 'uppercase',
              }}
            >
              Status
            </TableCell>
            <TableCell
              sx={{
                bgcolor: 'surfaceContainerLow',
                borderBottom: 1,
                borderColor: 'outlineVariant',
                typography: 'labelMono',
                color: 'onSurfaceVariant',
                textTransform: 'uppercase',
              }}
            >
              Groups
            </TableCell>
            <TableCell
              sx={{
                bgcolor: 'surfaceContainerLow',
                borderBottom: 1,
                borderColor: 'outlineVariant',
                typography: 'labelMono',
                color: 'onSurfaceVariant',
                textTransform: 'uppercase',
              }}
            >
              Roles
            </TableCell>
            <TableCell
              sx={{
                bgcolor: 'surfaceContainerLow',
                borderBottom: 1,
                borderColor: 'outlineVariant',
                typography: 'labelMono',
                color: 'onSurfaceVariant',
                textTransform: 'uppercase',
              }}
            >
              Last Active
            </TableCell>
            <TableCell
              sx={{
                bgcolor: 'surfaceContainerLow',
                borderBottom: 1,
                borderColor: 'outlineVariant',
              }}
            />
          </TableRow>
        </TableHead>
        <TableBody>
          {usersLoading &&
            Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={`skeleton-${i}`}>
                <TableCell colSpan={7} sx={{ py: 0.5, border: 0 }}>
                  <Skeleton
                    height={48}
                    sx={{ bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}
                  />
                </TableCell>
              </TableRow>
            ))}
          {!usersLoading && users.length === 0 && (
            <TableRow>
              <TableCell colSpan={7}>
                <Typography
                  variant="bodyMain"
                  sx={{ color: 'onSurfaceVariant', py: 4, textAlign: 'center', display: 'block' }}
                >
                  No users found
                </Typography>
              </TableCell>
            </TableRow>
          )}
          {!usersLoading &&
            users.map((user, index) => {
            const isSelected = selectedIds.includes(user.id)
            return (
              <TableRow
                key={user.id}
                hover
                selected={isSelected}
                onClick={() => onRowClick(user)}
                sx={{
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  backgroundColor: index % 2 !== 0 ? 'surfaceContainerLowest' : 'transparent',
                  '& .MuiTableCell-root': {
                    borderBottom: '1px solid',
                    borderColor: 'outlineVariant',
                  },
                  '&.MuiTableRow-hover:hover': {
                    backgroundColor: 'surfaceContainerLow',
                    '& .more-actions': { opacity: 1 },
                  },
                  '&.Mui-selected': {
                    backgroundColor: 'surfaceContainerHigh',
                  },
                  '&.Mui-selected:hover': {
                    backgroundColor: 'surfaceContainerHigh',
                  },
                }}
              >
                <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={isSelected}
                    onChange={() => onSelectOne(user.id)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Avatar
                      variant="rounded"
                      sx={{
                        width: 32,
                        height: 32,
                        bgcolor:
                          user.status === 'Active' ? 'secondaryContainer' : 'surfaceContainerHigh',
                        color:
                          user.status === 'Active' ? 'onSecondaryContainer' : 'onSurfaceVariant',
                        fontWeight: 'bold',
                        fontSize: '0.875rem',
                        border: 1,
                        borderColor: 'outlineVariant',
                        borderRadius: 1,
                      }}
                    >
                      {user.initials}
                    </Avatar>
                    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                      <Typography
                        variant="bodyData"
                        sx={{ fontWeight: 'bold', color: 'text.primary', lineHeight: 1.2 }}
                      >
                        {user.name}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{ color: 'onSurfaceVariant', lineHeight: 1.2 }}
                      >
                        {user.email}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <StatusChip
                    label={user.status}
                    color={user.status === 'Active' ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {user.groups.map((group) => (
                      <GroupChip key={group} label={group} />
                    ))}
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {user.roles.map((role) => (
                      <RoleChip key={role} label={role} />
                    ))}
                  </Box>
                </TableCell>
                <TableCell sx={{ color: 'onSurfaceVariant', typography: 'bodyData' }}>
                  {user.lastActive}
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    className="more-actions"
                    size="small"
                    sx={{
                      color: 'onSurfaceVariant',
                      opacity: 0,
                      transition: 'opacity 0.2s',
                    }}
                  >
                    <span className="material-symbols-outlined">more_vert</span>
                  </IconButton>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default UserTable
