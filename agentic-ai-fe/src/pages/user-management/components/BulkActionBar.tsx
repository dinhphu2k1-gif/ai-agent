import { Box, Paper, Typography, Button, Fade } from '@mui/material'

interface BulkActionBarProps {
  selectedCount: number
  onClear: () => void
  onBulkGroupClick: () => void
  onBulkRoleClick: () => void
  onBulkDeactivateClick: () => void
}

const BulkActionBar = ({
  selectedCount,
  onBulkGroupClick,
  onBulkRoleClick,
  onBulkDeactivateClick,
}: BulkActionBarProps) => {
  return (
    <Fade in={selectedCount > 0}>
      <Paper
        sx={{
          position: 'absolute',
          bottom: 24,
          left: '50%',
          transform: 'translateX(-50%)',
          bgcolor: 'surfaceContainerHigh',
          border: 1,
          borderColor: 'outlineVariant',
          px: 2,
          py: 1.5,
          borderRadius: 10, // Pill shape
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          zIndex: 30,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            pr: 2,
            borderRight: 1,
            borderColor: 'outlineVariant',
          }}
        >
          <Box
            sx={{
              width: 20,
              height: 20,
              borderRadius: 1,
              bgcolor: 'primary.main',
              color: 'onPrimary',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '12px',
              fontWeight: 'bold',
            }}
          >
            {selectedCount}
          </Box>
          <Typography variant="bodyData" sx={{ color: 'onSurface', fontWeight: 'bold' }}>
            selected
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            onClick={onBulkGroupClick}
            startIcon={
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                group_add
              </span>
            }
            sx={{
              color: 'onSurface',
              bgcolor: 'surfaceVariant',
              '&:hover': { bgcolor: 'surfaceBright' },
              textTransform: 'none',
              typography: 'bodyData',
              px: 1.5,
              borderRadius: 1,
            }}
          >
            Assign Group
          </Button>
          <Button
            size="small"
            onClick={onBulkRoleClick}
            startIcon={
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                admin_panel_settings
              </span>
            }
            sx={{
              color: 'onSurface',
              bgcolor: 'surfaceVariant',
              '&:hover': { bgcolor: 'surfaceBright' },
              textTransform: 'none',
              typography: 'bodyData',
              px: 1.5,
              borderRadius: 1,
            }}
          >
            Assign Role
          </Button>
          <Button
            size="small"
            onClick={onBulkDeactivateClick}
            startIcon={
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                block
              </span>
            }
            sx={{
              color: 'error.main',
              bgcolor: 'surfaceVariant',
              '&:hover': { bgcolor: 'surfaceBright' },
              textTransform: 'none',
              typography: 'bodyData',
              px: 1.5,
              borderRadius: 1,
            }}
          >
            Deactivate
          </Button>
        </Box>
      </Paper>
    </Fade>
  )
}

export default BulkActionBar
