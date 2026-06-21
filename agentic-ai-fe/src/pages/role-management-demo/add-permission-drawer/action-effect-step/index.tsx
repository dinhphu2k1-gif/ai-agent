import { Box, Typography } from '@mui/material'
import { PermissionEffect } from '../../types'
import { AVAILABLE_ACTIONS } from '../../constants'

interface ActionEffectStepProps {
  selectedActions: string[]
  onChangeActions: (actions: string[]) => void
  effect: PermissionEffect
  onChangeEffect: (effect: PermissionEffect) => void
}

const ActionEffectStep = ({
  selectedActions,
  onChangeActions,
  effect,
  onChangeEffect,
}: ActionEffectStepProps) => {
  const handleToggleAction = (name: string) => {
    if (selectedActions.includes(name)) {
      onChangeActions(selectedActions.filter((a) => a !== name))
    } else {
      onChangeActions([...selectedActions, name])
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Select Actions */}
      <Box>
        <Typography variant="headlineAgent" sx={{ color: 'onSurface', mb: 1.5 }}>
          Select actions
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
          {AVAILABLE_ACTIONS.map((action) => {
            const isSelected = selectedActions.includes(action.name)
            return (
              <Box
                key={action.name}
                onClick={() => handleToggleAction(action.name)}
                sx={{
                  position: 'relative',
                  p: 1.5,
                  borderRadius: 3,
                  bgcolor: isSelected ? 'secondaryContainer' : 'surfaceContainer',
                  border: 1,
                  borderColor: isSelected ? 'secondary.main' : 'outlineVariant',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1,
                  transition: 'all 0.2s',
                  '&:hover': {
                    bgcolor: isSelected ? 'secondaryContainer' : 'surfaceContainerHighest',
                  },
                }}
              >
                <span
                  className="material-symbols-outlined"
                  style={{
                    fontSize: 20,
                    color: isSelected
                      ? 'var(--mui-palette-onSecondaryContainer)'
                      : 'var(--mui-palette-onSurfaceVariant)',
                  }}
                >
                  {action.icon}
                </span>
                <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                  <Typography
                    variant="labelMono"
                    sx={{
                      fontWeight: 'bold',
                      color: isSelected ? 'onSecondaryContainer' : 'onSurface',
                    }}
                  >
                    {action.name}
                  </Typography>
                  <Typography variant="caption" sx={{ fontSize: 10, color: 'onSurfaceVariant' }}>
                    {action.description}
                  </Typography>
                </Box>

                {isSelected && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      bgcolor: 'secondary.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <span
                      className="material-symbols-outlined"
                      style={{ fontSize: 12, color: 'var(--mui-palette-onSecondary)' }}
                    >
                      check
                    </span>
                  </Box>
                )}
              </Box>
            )
          })}
        </Box>
      </Box>

      {/* Effect */}
      <Box>
        <Typography variant="headlineAgent" sx={{ color: 'onSurface', mb: 1.5 }}>
          Effect
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
          {/* ALLOW */}
          <Box
            onClick={() => onChangeEffect(PermissionEffect.Allow)}
            sx={{
              position: 'relative',
              p: 2,
              borderRadius: 3,
              bgcolor: effect === PermissionEffect.Allow ? 'statusActiveBg' : 'surfaceContainer',
              border: effect === PermissionEffect.Allow ? 2 : 1,
              borderColor:
                effect === PermissionEffect.Allow ? 'statusActiveBorder' : 'outlineVariant',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
              overflow: 'hidden',
              transition: 'all 0.2s',
              '&:hover': {
                bgcolor:
                  effect === PermissionEffect.Allow ? 'statusActiveBg' : 'surfaceContainerHighest',
              },
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                left: 0,
                top: 0,
                bottom: 0,
                width: 4,
                bgcolor: 'success.main',
              }}
            />
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                color:
                  effect === PermissionEffect.Allow ? 'statusActiveText' : 'onSurfaceVariant',
              }}
            >
              <span
                className="material-symbols-outlined"
                style={{
                  fontVariationSettings: effect === PermissionEffect.Allow ? "'FILL' 1" : undefined,
                  fontSize: 20,
                }}
              >
                shield_check
              </span>
              <Typography variant="labelMono" sx={{ fontWeight: 'bold' }}>
                ALLOW
              </Typography>
            </Box>
            <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }}>
              Grant access — overridden by any DENY
            </Typography>
          </Box>

          {/* DENY */}
          <Box
            onClick={() => onChangeEffect(PermissionEffect.Deny)}
            sx={{
              position: 'relative',
              p: 2,
              borderRadius: 3,
              bgcolor: effect === PermissionEffect.Deny ? 'errorContainer' : 'surfaceContainer',
              border: effect === PermissionEffect.Deny ? 2 : 1,
              borderColor: effect === PermissionEffect.Deny ? 'error.main' : 'outlineVariant',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
              overflow: 'hidden',
              transition: 'all 0.2s',
              '&:hover': {
                bgcolor:
                  effect === PermissionEffect.Deny ? 'errorContainer' : 'surfaceContainerHighest',
              },
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                left: 0,
                top: 0,
                bottom: 0,
                width: 4,
                bgcolor: 'error.main',
              }}
            />
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                color: effect === PermissionEffect.Deny ? 'onErrorContainer' : 'onSurfaceVariant',
              }}
            >
              <span
                className="material-symbols-outlined"
                style={{
                  fontVariationSettings: effect === PermissionEffect.Deny ? "'FILL' 1" : undefined,
                  fontSize: 20,
                }}
              >
                gpp_bad
              </span>
              <Typography variant="labelMono" sx={{ fontWeight: 'bold' }}>
                DENY
              </Typography>
            </Box>
            <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }}>
              Block access — wins over all ALLOW sources
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  )
}

export default ActionEffectStep
