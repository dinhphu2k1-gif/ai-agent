import { useState } from 'react'
import { Box, Typography, IconButton, Collapse } from '@mui/material'
import type { InheritedSummary } from '../types'

interface InheritedPermissionsSummaryProps {
  summary: InheritedSummary
}

const InheritedPermissionsSummary = ({ summary }: InheritedPermissionsSummaryProps) => {
  const [expanded, setExpanded] = useState(false)

  const summaryLine = `${summary.permissionCount} permissions across ${summary.resourceTypeCount} resources from ${summary.roleCount} roles`

  return (
    <Box
      sx={{
        borderTop: 1,
        borderColor: 'outlineVariant',
        bgcolor: 'surfaceContainerLow',
        px: 2,
        py: 1,
      }}
    >
      <Box
        component="button"
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        sx={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
          p: 0,
          border: 0,
          bgcolor: 'transparent',
          cursor: 'pointer',
          color: 'onSurfaceVariant',
          textAlign: 'left',
          '&:hover': { color: 'onSurface' },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
            account_tree
          </span>
          <Typography variant="bodyData" sx={{ color: 'inherit' }}>
            Inherited permissions summary
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant', display: { xs: 'none', sm: 'block' } }}>
            {summaryLine}
          </Typography>
          <IconButton
            size="small"
            aria-label={expanded ? 'Collapse summary' : 'Expand summary'}
            tabIndex={-1}
            sx={{
              p: 0,
              color: 'inherit',
              transform: expanded ? 'rotate(180deg)' : 'none',
              transition: 'transform 0.2s ease',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
              expand_more
            </span>
          </IconButton>
        </Box>
      </Box>
      <Collapse in={expanded}>
        <Typography variant="caption" sx={{ color: 'onSurfaceVariant', display: { xs: 'block', sm: 'none' }, mt: 1, pl: 3.5 }}>
          {summaryLine}
        </Typography>
        <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', mt: 1, pl: 3.5 }}>
          Effective access is the union of all permissions granted by roles assigned to this group.
          Members inherit these permissions in addition to any direct user-level roles.
        </Typography>
      </Collapse>
    </Box>
  )
}

export default InheritedPermissionsSummary
