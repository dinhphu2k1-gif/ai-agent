import { Box, Grid, Skeleton, Stack } from '@mui/material'
import type { UserGroup } from '../types'
import GroupListHeader from './GroupListHeader'
import GroupListItem from './GroupListItem'

interface GroupListPanelProps {
  groups: UserGroup[]
  selectedGroupId: string | null
  searchQuery: string
  loading?: boolean
  onSearchChange: (value: string) => void
  onSelectGroup: (groupId: string) => void
  onAddGroup: () => void
}

const GroupListPanel = ({
  groups,
  selectedGroupId,
  searchQuery,
  loading,
  onSearchChange,
  onSelectGroup,
  onAddGroup,
}: GroupListPanelProps) => {
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
      <GroupListHeader
        searchQuery={searchQuery}
        onSearchChange={onSearchChange}
        onAddGroup={onAddGroup}
      />
      <Box sx={{ flex: 1, overflowY: 'auto', p: 1 }}>
        <Stack spacing={0.5}>
          {loading && groups.length === 0
            ? [1, 2, 3].map((key) => (
                <Skeleton
                  key={key}
                  variant="rounded"
                  height={72}
                  sx={{ bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}
                />
              ))
            : null}
          {groups.map((group) => (
            <GroupListItem
              key={group.id}
              group={group}
              selected={group.id === selectedGroupId}
              onSelect={() => onSelectGroup(group.id)}
            />
          ))}
        </Stack>
      </Box>
    </Grid>
  )
}

export default GroupListPanel
