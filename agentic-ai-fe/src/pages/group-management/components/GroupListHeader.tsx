import { Box, Typography, TextField, Button, InputAdornment } from '@mui/material'

interface GroupListHeaderProps {
  searchQuery: string
  onSearchChange: (value: string) => void
  onAddGroup: () => void
}

const GroupListHeader = ({ searchQuery, onSearchChange, onAddGroup }: GroupListHeaderProps) => {
  return (
    <Box
      sx={{
        p: 2,
        borderBottom: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surface',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
          Groups
        </Typography>
        <Button
          size="small"
          onClick={onAddGroup}
          startIcon={
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
              add
            </span>
          }
          sx={{
            textTransform: 'none',
            fontWeight: 500,
            fontSize: 13,
            color: 'onTertiary',
            bgcolor: 'tertiary',
            borderRadius: 1,
            px: 1.5,
            py: 0.75,
            minWidth: 'auto',
            boxShadow: 'none',
            '&:hover': { bgcolor: 'tertiaryFixedDim', boxShadow: 'none' },
          }}
        >
          New Group
        </Button>
      </Box>
      <TextField
        size="small"
        fullWidth
        placeholder="Search groups..."
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        sx={{ mt: 0.5 }}
        slotProps={{
          input: {
            sx: { fontSize: 13 },
            startAdornment: (
              <InputAdornment position="start">
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: 18, color: 'var(--mui-palette-onSurfaceVariant)' }}
                >
                  search
                </span>
              </InputAdornment>
            ),
          },
        }}
      />
    </Box>
  )
}

export default GroupListHeader
