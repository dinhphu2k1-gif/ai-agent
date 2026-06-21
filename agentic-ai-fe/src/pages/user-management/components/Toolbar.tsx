import { Box, TextField, Button, InputAdornment } from '@mui/material'

interface ToolbarProps {
  searchValue: string
  onSearchChange: (value: string) => void
  onAddClick: () => void
}

const Toolbar = ({ searchValue, onSearchChange, onAddClick }: ToolbarProps) => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        bgcolor: 'surfaceContainer',
        borderRadius: 2,
        p: 1.5,
        border: 1,
        borderColor: 'outlineVariant',
        shrink: 0,
        boxShadow: 1,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
        <TextField
          placeholder="Search users..."
          size="small"
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          sx={{
            width: 256,
            '& .MuiOutlinedInput-root': {
              bgcolor: 'surfaceContainer',
              '& fieldset': { borderColor: 'outlineVariant' },
            },
          }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                    search
                  </span>
                </InputAdornment>
              ),
            },
          }}
        />
        <Button
          variant="outlined"
          size="small"
          startIcon={<span className="material-symbols-outlined">filter_list</span>}
          endIcon={<span className="material-symbols-outlined">arrow_drop_down</span>}
          sx={{
            bgcolor: 'surfaceContainerHigh',
            borderColor: 'outlineVariant',
            color: 'text.primary',
            textTransform: 'none',
            '&:hover': { bgcolor: 'surfaceContainerHighest' },
          }}
        >
          Status: All
        </Button>
      </Box>

      <Button
        variant="contained"
        color="success"
        onClick={onAddClick}
        startIcon={
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
            person_add
          </span>
        }
        sx={{
          textTransform: 'none',
          fontWeight: 600,
          typography: 'headlineAgent',
          px: 2,
          py: 0.75,
        }}
      >
        Add User
      </Button>
    </Box>
  )
}

export default Toolbar
