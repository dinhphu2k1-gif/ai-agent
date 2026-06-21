import { Box, Typography, Button } from '@mui/material'

interface PermissionListPanelProps {
  role: string
  onAddPermission: () => void
}

const PermissionListPanel = ({ role, onAddPermission }: PermissionListPanelProps) => {
  return (
    <Box
      sx={{
        width: '45%',
        bgcolor: 'surface',
        borderRight: 1,
        borderColor: 'outlineVariant',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Role Header */}
      <Box
        sx={{
          p: 3,
          borderBottom: 1,
          borderColor: 'outlineVariant',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box
              sx={{
                width: 40,
                height: 40,
                minWidth: 40,
                minHeight: 40,
                borderRadius: 2,
                bgcolor: 'surfaceContainerHighest',
                border: 1,
                borderColor: 'outlineVariant',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span
                className="material-symbols-outlined"
                style={{
                  color: 'var(--mui-palette-tertiary)',
                  fontVariationSettings: "'FILL' 1",
                }}
              >
                badge
              </span>
            </Box>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="displaySm" sx={{ color: 'onSurface' }}>
                  {role}
                </Typography>
                <Box
                  sx={{
                    px: 1,
                    py: 0.25,
                    borderRadius: 4,
                    bgcolor: 'tertiaryContainer',
                    color: 'onTertiaryContainer',
                  }}
                >
                  <Typography variant="caption">Role</Typography>
                </Box>
              </Box>
              <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', mt: 0.5 }}>
                Data analysis and reporting permissions.
              </Typography>
            </Box>
          </Box>
          <Button
            variant="contained"
            onClick={onAddPermission}
            sx={{
              bgcolor: 'primary.main',
              color: 'onPrimary',
              typography: 'headlineAgent',
              borderRadius: 2,
              textTransform: 'none',
              px: 2,
              py: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              '&:hover': { bgcolor: 'primary.dark' },
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
              add
            </span>{' '}
            Add Permission
          </Button>
        </Box>
      </Box>

      {/* Permission Cards */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Existing Permission Card Mockup */}
          <Box
            sx={{
              p: 2,
              borderRadius: 3,
              bgcolor: 'surfaceContainer',
              border: 1,
              borderColor: 'outlineVariant',
              display: 'flex',
              flexDirection: 'column',
              gap: 1.5,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  color: 'onSurfaceVariant',
                }}
              >
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: 16, color: 'var(--mui-palette-secondary-main)' }}
                >
                  database
                </span>
                <Typography variant="caption">analytics_db</Typography>
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  chevron_right
                </span>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  folder
                </span>
                <Typography variant="caption">public</Typography>
              </Box>
              <Box
                sx={{
                  px: 1,
                  py: 0.5,
                  bgcolor: 'success.main',
                  color: 'success.contrastText',
                  border: 1,
                  borderColor: 'success.main',
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  check_circle
                </span>
                <Typography variant="labelMono">ALLOW</Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
                sales_data
              </Typography>
              <Box
                sx={{
                  px: 0.75,
                  py: 0.25,
                  bgcolor: 'surfaceContainerHighest',
                  color: 'onSurfaceVariant',
                  border: 1,
                  borderColor: 'outlineVariant',
                  borderRadius: 1,
                }}
              >
                <Typography variant="labelMono" sx={{ fontSize: 10 }}>
                  TABLE
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              {['SELECT', 'DESCRIBE'].map((action) => (
                <Box
                  key={action}
                  sx={{
                    px: 1,
                    py: 0.5,
                    bgcolor: 'surfaceContainerHigh',
                    color: 'onSurface',
                    border: 1,
                    borderColor: 'outlineVariant',
                    borderRadius: 1,
                  }}
                >
                  <Typography variant="labelMono">{action}</Typography>
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  )
}

export default PermissionListPanel
