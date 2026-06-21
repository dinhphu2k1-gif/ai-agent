import React from 'react'
import { Box, Typography } from '@mui/material'

interface PermissionStepperProps {
  steps: string[]
  activeStep: number
}

const PermissionStepper = ({ steps, activeStep }: PermissionStepperProps) => {
  return (
    <Box
      sx={{
        px: 3,
        py: 2,
        borderBottom: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surface',
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        overflowX: 'auto',
        '&::-webkit-scrollbar': { display: 'none' },
      }}
    >
      {steps.map((step, index) => {
        const isActive = index === activeStep
        const isPast = index < activeStep

        return (
          <React.Fragment key={step}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                color: isActive ? 'primary.main' : isPast ? 'onSurface' : 'onSurfaceVariant',
              }}
            >
              <Box
                sx={{
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  bgcolor: isActive
                    ? 'primaryContainer'
                    : isPast
                      ? 'primary.main'
                      : 'surfaceContainerHigh',
                  color: isActive ? 'onPrimaryContainer' : isPast ? 'onPrimary' : 'inherit',
                  border: isActive || isPast ? 0 : 1,
                  borderColor: 'outlineVariant',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {isPast ? (
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                    check
                  </span>
                ) : (
                  <Typography variant="labelMono" sx={{ fontWeight: isActive ? 'bold' : 'normal' }}>
                    {index + 1}
                  </Typography>
                )}
              </Box>
              <Typography variant={isActive ? 'h6' : 'bodyData'} sx={{ whiteSpace: 'nowrap' }}>
                {step}
              </Typography>
            </Box>
          </React.Fragment>
        )
      })}
    </Box>
  )
}

export default PermissionStepper
