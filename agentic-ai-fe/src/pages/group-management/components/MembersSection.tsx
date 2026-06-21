import { useMemo, useState } from 'react'
import { Box, Typography, Button, TextField, InputAdornment, Skeleton, Stack } from '@mui/material'
import type { GroupMember } from '../types'
import MemberRow from './MemberRow'

interface MembersSectionProps {
  members: GroupMember[]
  loading?: boolean
  assignDisabled: boolean
  onAddMember: () => void
  onRemoveMember: (memberId: string) => void
}

const MembersSection = ({
  members,
  loading = false,
  assignDisabled,
  onAddMember,
  onRemoveMember,
}: MembersSectionProps) => {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredMembers = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return members
    return members.filter(
      (member) =>
        member.name.toLowerCase().includes(q) || member.email.toLowerCase().includes(q)
    )
  }, [members, searchQuery])

  return (
    <Box
      sx={{
        border: 1,
        borderColor: 'outlineVariant',
        borderRadius: 3,
        bgcolor: 'surfaceContainer',
        overflow: 'hidden',
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
            Members
          </Typography>
          <Box
            sx={{
              px: 1,
              py: 0.25,
              borderRadius: 999,
              bgcolor: 'surfaceBright',
              color: 'onSurface',
            }}
          >
            <Typography variant="labelMono" component="span" sx={{ fontSize: 12 }}>
              {members.length}
            </Typography>
          </Box>
        </Box>
        <Button
          size="small"
          disabled={assignDisabled}
          onClick={onAddMember}
          startIcon={
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
              person_add
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
          Add member
        </Button>
      </Box>

      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'outlineVariant' }}>
        <TextField
          size="small"
          fullWidth
          placeholder="Search members..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          slotProps={{
            input: {
              sx: { fontSize: 13, bgcolor: 'surface' },
              startAdornment: (
                <InputAdornment position="start">
                  <span
                    className="material-symbols-outlined"
                    style={{ fontSize: 16, color: 'var(--mui-palette-onSurfaceVariant)' }}
                  >
                    search
                  </span>
                </InputAdornment>
              ),
            },
          }}
        />
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        {loading ? (
          <Stack spacing={1} sx={{ p: 2 }}>
            {[1, 2, 3].map((key) => (
              <Skeleton
                key={key}
                variant="rounded"
                height={56}
                sx={{ bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}
              />
            ))}
          </Stack>
        ) : filteredMembers.length === 0 ? (
          <Typography
            variant="bodyData"
            sx={{ color: 'onSurfaceVariant', py: 3, px: 2, textAlign: 'center' }}
          >
            {members.length === 0
              ? 'No members in this group yet'
              : 'No members match your search'}
          </Typography>
        ) : (
          filteredMembers.map((member, index) => (
            <MemberRow
              key={member.id}
              member={member}
              avatarVariant={index % 2 === 0 ? 'primary' : 'secondary'}
              onRemove={() => onRemoveMember(member.id)}
            />
          ))
        )}
      </Box>
    </Box>
  )
}

export default MembersSection
