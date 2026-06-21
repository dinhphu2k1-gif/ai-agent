import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Button,
  TextField,
  InputAdornment,
  Stack,
  Checkbox,
  Avatar,
  styled,
} from '@mui/material'
import { useEffect, useState } from 'react'
import type { User } from './UserTable'

export interface BulkGroupOption {
  id: string
  name: string
  members: number
  description: string
}

interface AddGroupDrawerProps {
  open: boolean
  onClose: () => void
  selectedUsers: User[]
  groups: BulkGroupOption[]
  optionsLoading?: boolean
  submitting?: boolean
  onAssign: (groupNames: string[]) => void | Promise<void>
}

const GroupItem = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'selected',
})<{ selected?: boolean }>(({ theme, selected }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  gap: theme.spacing(1.5),
  padding: theme.spacing(1.5),
  backgroundColor: 'var(--mui-palette-surface)',
  borderRadius: theme.shape.borderRadius,
  border: '1px solid',
  borderColor: selected ? 'var(--mui-palette-primary-main)' : 'var(--mui-palette-outlineVariant)',
  cursor: 'pointer',
  transition: 'all 0.2s',
  position: 'relative',
  overflow: 'hidden',
  '&:hover': {
    backgroundColor: 'var(--mui-palette-surfaceContainerHighest)',
  },
  ...(selected && {
    '&::before': {
      content: '""',
      position: 'absolute',
      left: 0,
      top: 0,
      bottom: 0,
      width: 3,
      backgroundColor: 'var(--mui-palette-primary-main)',
    },
  }),
}))

const AddGroupDrawer = ({
  open,
  onClose,
  selectedUsers,
  groups,
  optionsLoading = false,
  submitting = false,
  onAssign,
}: AddGroupDrawerProps) => {
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    if (!open) {
      setSelectedGroupIds([])
      setSearchQuery('')
    }
  }, [open])

  const handleToggleGroup = (id: string) => {
    setSelectedGroupIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const filteredGroups = groups.filter((g) =>
    g.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleAssign = async () => {
    const selectedNames = groups
      .filter((g) => selectedGroupIds.includes(g.id))
      .map((g) => g.name)

    try {
      await onAssign(selectedNames)
      onClose()
    } catch {
      // Parent shows toast; keep drawer open
    }
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      slotProps={{
        paper: {
          sx: {
            width: 450,
            bgcolor: 'var(--mui-palette-surfaceContainerLow)',
            backgroundImage: 'none',
          },
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surface)',
        }}
      >
        <Typography variant="headlineAgent">Gán Nhóm Người Dùng</Typography>
        <IconButton onClick={onClose} size="small">
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      {/* Body */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
        <Stack spacing={3}>
          {/* Selected Users */}
          <Box>
            <Typography
              variant="labelMono"
              sx={{ color: 'var(--mui-palette-onSurfaceVariant)', mb: 1, display: 'block' }}
            >
              SELECTED USERS ({selectedUsers.length})
            </Typography>
            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 1,
                p: 1,
                bgcolor: 'var(--mui-palette-surface)',
                borderRadius: 1,
                border: 1,
                borderColor: 'var(--mui-palette-outlineVariant)',
              }}
            >
              {selectedUsers.map((user) => (
                <Box
                  key={user.id}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                    bgcolor: 'var(--mui-palette-surfaceContainerHighest)',
                    px: 1,
                    py: 0.5,
                    borderRadius: 1,
                  }}
                >
                  <Avatar sx={{ width: 20, height: 20, fontSize: 10 }}>{user.initials}</Avatar>
                  <Typography variant="caption">{user.name}</Typography>
                </Box>
              ))}
            </Box>
          </Box>

          {/* Groups Selection */}
          <Box>
            <Typography
              variant="labelMono"
              sx={{ color: 'var(--mui-palette-onSurfaceVariant)', mb: 1, display: 'block' }}
            >
              AVAILABLE GROUPS
            </Typography>
            <TextField
              fullWidth
              size="small"
              placeholder="Search groups..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              sx={{
                mb: 2,
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'var(--mui-palette-surface)',
                },
              }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                        search
                      </span>
                    </InputAdornment>
                  ),
                },
              }}
            />

            <Stack spacing={1}>
              {filteredGroups.map((group) => {
                const isSelected = selectedGroupIds.includes(group.id)
                return (
                  <GroupItem
                    key={group.id}
                    selected={isSelected}
                    onClick={() => handleToggleGroup(group.id)}
                  >
                    <Checkbox
                      checked={isSelected}
                      size="small"
                      sx={{ p: 0, mt: 0.5 }}
                      onClick={(e) => e.stopPropagation()}
                      onChange={() => handleToggleGroup(group.id)}
                    />
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="headlineAgent" sx={{ fontSize: 14 }}>
                          {group.name}
                        </Typography>
                        <Box
                          sx={{
                            bgcolor: 'var(--mui-palette-surfaceContainer)',
                            px: 1,
                            borderRadius: 0.5,
                          }}
                        >
                          <Typography variant="labelMono" sx={{ fontSize: 10 }}>
                            {group.members} members
                          </Typography>
                        </Box>
                      </Box>
                      <Typography
                        variant="bodyData"
                        sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}
                      >
                        {group.description}
                      </Typography>
                    </Box>
                  </GroupItem>
                )
              })}
            </Stack>
          </Box>
        </Stack>
      </Box>

      {/* Footer */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surface)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 1,
        }}
      >
        <Button
          onClick={onClose}
          variant="outlined"
          sx={{
            color: 'var(--mui-palette-onSurfaceVariant)',
            textTransform: 'none',
            fontWeight: 600,
          }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={() => void handleAssign()}
          disabled={submitting || optionsLoading || selectedGroupIds.length === 0}
          startIcon={<span className="material-symbols-outlined">check</span>}
          sx={{
            textTransform: 'none',
            fontWeight: 600,
          }}
        >
          Assign to Groups
        </Button>
      </Box>
    </Drawer>
  )
}

export default AddGroupDrawer
