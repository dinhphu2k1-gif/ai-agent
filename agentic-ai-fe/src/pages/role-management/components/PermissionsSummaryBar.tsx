import { Box, Typography } from '@mui/material'
import type { PermissionSummary } from '../types'

interface PermissionsSummaryBarProps {
  summary: PermissionSummary
}

const PermissionsSummaryBar = ({ summary }: PermissionsSummaryBarProps) => {
  return (
    <Box
      sx={{
        p: 1.5,
        borderTop: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surface',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 1.5,
        flexShrink: 0,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Typography variant="bodyData" sx={{ color: 'onSurface', fontWeight: 600 }}>
          Total: {summary.total} permissions
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: 'success.main',
            }}
          />
          <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }}>
            {summary.allowCount} ALLOW
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'error.main' }} />
          <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }}>
            {summary.denyCount} DENY
          </Typography>
        </Box>
      </Box>
      {summary.modifierCount > 0 && (
        <Typography
          variant="bodyData"
          sx={{ color: 'onSurfaceVariant', fontStyle: 'italic', opacity: 0.7 }}
        >
          {summary.modifierCount} with modifiers
        </Typography>
      )}
    </Box>
  )
}

export default PermissionsSummaryBar
