import { Box, Typography, IconButton } from '@mui/material'
import type { UserGroup } from '../types'

interface GroupDetailHeaderProps {
  group: UserGroup | null
  onDeleteGroup: () => void
}

const GroupDetailHeader = ({ group, onDeleteGroup }: GroupDetailHeaderProps) => {
  return (
    <Box
      sx={{
        p: 2,
        borderBottom: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surface',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexShrink: 0,
        gap: 2,
      }}
    >
      {group ? (
        <>
          <Box sx={{ minWidth: 0, display: 'flex', flexDirection: 'column' }}>
            <Typography variant="displaySm" sx={{ color: 'onSurface' }} noWrap>
              {group.name}
            </Typography>
            {group.description && (
              <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', mt: 0.5 }}>
                {group.description}
              </Typography>
            )}
            <Typography variant="caption" sx={{ color: 'onSurfaceVariant', mt: 0.75, display: 'block' }}>
              Created {group.createdAt}
            </Typography>
          </Box>
          <IconButton
            size="small"
            aria-label="Delete group"
            onClick={onDeleteGroup}
            sx={{
              color: 'onSurfaceVariant',
              border: 1,
              borderColor: 'outlineVariant',
              borderRadius: 1,
              '&:hover': { color: 'error.main', bgcolor: 'errorContainer' },
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
              delete
            </span>
          </IconButton>
        </>
      ) : (
        <Typography variant="displaySm" sx={{ color: 'onSurface' }}>
          Group Details
        </Typography>
      )}
    </Box>
  )
}

export default GroupDetailHeader
