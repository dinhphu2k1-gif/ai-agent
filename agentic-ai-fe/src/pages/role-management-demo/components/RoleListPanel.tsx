import { Box, Typography, TextField, InputAdornment } from '@mui/material'

interface RoleListPanelProps {
  selectedRole: string
  onSelect: (role: string) => void
}

const ROLES = [
  { name: 'admin', dotColor: 'secondary.main' },
  { name: 'analyst', dotColor: 'tertiary.main' },
  { name: 'viewer', dotColor: 'outline' },
]

const RoleListPanel = ({ selectedRole, onSelect }: RoleListPanelProps) => {
  return (
    <Box
      sx={{
        width: '25%',
        minWidth: 250,
        bgcolor: 'surfaceContainer',
        borderRight: 1,
        borderColor: 'outlineVariant',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'outlineVariant' }}>
        <TextField
          placeholder="Search roles..."
          fullWidth
          disabled
          variant="outlined"
          size="small"
          sx={{
            '& .MuiOutlinedInput-root': {
              bgcolor: 'surfaceContainerHigh',
              borderRadius: 2,
              color: 'onSurface',
            },
          }}
          slotProps={{
            input: {
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

      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 0.5,
        }}
      >
        {ROLES.map((role) => {
          const isSelected = role.name === selectedRole
          return (
            <Box
              key={role.name}
              onClick={() => onSelect(role.name)}
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: isSelected ? 'surfaceContainerHighest' : 'transparent',
                border: isSelected ? 1 : 0,
                borderColor: 'outlineVariant',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                opacity: !isSelected ? 0.5 : 1,
                '&:hover': { opacity: 1, bgcolor: 'surfaceContainerHighest' },
                transition: 'all 0.15s',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: role.dotColor,
                  }}
                />
                <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
                  {role.name}
                </Typography>
              </Box>
              {isSelected && (
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: 16, color: 'var(--mui-palette-onSurfaceVariant)' }}
                >
                  chevron_right
                </span>
              )}
            </Box>
          )
        })}
      </Box>
    </Box>
  )
}

export default RoleListPanel
