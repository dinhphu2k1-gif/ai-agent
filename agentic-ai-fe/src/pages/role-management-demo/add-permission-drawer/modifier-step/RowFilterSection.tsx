import { Box, Typography, Switch, Button, IconButton } from '@mui/material'

interface RowFilterSectionProps {
  rowFilterEnabled: boolean
  onChangeRowFilterEnabled: (enabled: boolean) => void
  conditionExpression: string
  onChangeConditionExpression: (expr: string) => void
}

const RowFilterSection = ({
  rowFilterEnabled,
  onChangeRowFilterEnabled,
  conditionExpression,
  onChangeConditionExpression,
}: RowFilterSectionProps) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Toggle Card */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          bgcolor: 'surfaceContainer',
          borderRadius: 1,
          border: 1,
          borderColor: 'outlineVariant',
        }}
      >
        <Box sx={{ flex: 1, pr: 2, display: 'flex', flexDirection: 'column' }}>
          <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
            Add row filter
          </Typography>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
            Restrict access to specific rows using a SQL-like expression
          </Typography>
        </Box>
        <Switch
          checked={rowFilterEnabled}
          onChange={(e) => onChangeRowFilterEnabled(e.target.checked)}
          color="primary"
        />
      </Box>

      {rowFilterEnabled && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Label */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="labelMono" sx={{ fontWeight: 'bold', color: 'onSurface' }}>
              condition_expr
            </Typography>
            <IconButton size="small" sx={{ color: 'onSurfaceVariant', p: 0.5 }}>
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                help_outline
              </span>
            </IconButton>
          </Box>

          {/* Quick Inserters */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            {['Insert column', 'Insert operator', 'Insert function'].map((label) => (
              <Button
                key={label}
                size="small"
                variant="outlined"
                sx={{
                  bgcolor: 'surfaceContainerHigh',
                  borderColor: 'outlineVariant',
                  color: 'onSurface',
                  textTransform: 'none',
                  fontSize: 12,
                  borderRadius: 1,
                  py: 0.5,
                  px: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                }}
              >
                {label}
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  expand_more
                </span>
              </Button>
            ))}
          </Box>

          {/* Code Editor */}
          <Box
            sx={{
              display: 'flex',
              border: 1,
              borderColor: 'outlineVariant',
              borderRadius: 2,
              overflow: 'hidden',
              bgcolor: 'surfaceContainerHighest',
            }}
          >
            <Box
              sx={{
                width: 40,
                bgcolor: 'surfaceContainerHigh',
                borderRight: 1,
                borderColor: 'outlineVariant',
                display: 'flex',
                justifyContent: 'center',
                py: 1.5,
              }}
            >
              <Typography
                variant="labelMono"
                sx={{ color: 'onSurfaceVariant', opacity: 0.5, fontSize: 11 }}
              >
                1
              </Typography>
            </Box>
            <Box
              component="textarea"
              value={conditionExpression}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                onChangeConditionExpression(e.target.value)
              }
              placeholder="e.g. region = 'North' AND status = 'active'"
              sx={{
                flex: 1,
                p: 1.5,
                bgcolor: 'transparent',
                border: 'none',
                color: 'onSurface',
                fontFamily: 'var(--mui-fontFamily-label-mono)',
                fontSize: 13,
                resize: 'none',
                minHeight: 96,
                outline: 'none',
                lineHeight: 1.5,
                '&::placeholder': { color: 'onSurfaceVariant', opacity: 0.3 },
              }}
            />
          </Box>

          {/* SQL Validation */}
          {conditionExpression.trim() && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'success.main' }}>
              <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                check_circle
              </span>
              <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                Valid SQL fragment
              </Typography>
            </Box>
          )}

          {/* Security Warning */}
          <Box
            sx={{
              p: 1.5,
              bgcolor: 'surfaceContainerLow',
              border: 1,
              borderColor: 'warning.main',
              borderRadius: 2,
              display: 'flex',
              gap: 1.5,
              alignItems: 'flex-start',
            }}
          >
            <span
              className="material-symbols-outlined"
              style={{ color: 'var(--mui-palette-warning-main)', fontSize: 20 }}
            >
              warning
            </span>
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <Typography variant="bodyData" sx={{ color: 'warning.main', fontWeight: 'bold' }}>
                Security Warning
              </Typography>
              <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
                Never build condition_expr from raw user input. Use hardcoded values or allowlisted
                constants only.
              </Typography>
            </Box>
          </Box>

          {/* Estimated Effect Banner */}
          <Box
            sx={{
              py: 1,
              px: 1.5,
              bgcolor: 'surfaceContainerLow',
              border: 1,
              borderColor: 'outlineVariant',
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              gap: 2,
            }}
          >
            <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
              Estimated effect:
            </Typography>
            <Box
              sx={{
                display: 'flex',
                gap: 2,
                fontFamily: 'var(--mui-fontFamily-label-mono)',
                fontSize: 11,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'onSurface' }}>
                rows matching:{' '}
                <Box component="span" sx={{ color: 'success.main' }}>
                  visible ✓
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'onSurface' }}>
                rows not matching:{' '}
                <Box component="span" sx={{ color: 'error.main' }}>
                  hidden ✗
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  )
}

export default RowFilterSection
