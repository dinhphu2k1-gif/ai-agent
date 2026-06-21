import { Box, Typography, Button } from '@mui/material'
import type { ResourceNode } from '../types'

interface NoModifierSectionProps {
  selectedPath: ResourceNode[] | null
  onGoToStep: (step: number) => void
  lockResource?: boolean
}

const NoModifierSection = ({ selectedPath, onGoToStep, lockResource }: NoModifierSectionProps) => {
  // Extract database name from path if available
  const dbNode = selectedPath?.find((node) => node.type === 'database')
  const schemaNode = selectedPath?.find((node) => node.type === 'schema')
  const resourceName = schemaNode?.name || dbNode?.name || 'analytics_db'

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Step Heading */}
      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        <Typography variant="headlineAgent" sx={{ color: 'onSurface', mb: 0.5 }}>
          Add Modifiers
        </Typography>
        <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant' }}>
          Refine access with row-level filtering or column masking.
        </Typography>
      </Box>

      {/* Main Illustration / No Modifiers Empty State */}
      <Box
        sx={{
          bgcolor: 'surfaceContainerLowest',
          border: '2px dashed',
          borderColor: 'outlineVariant',
          borderRadius: 3,
          p: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            bgcolor: 'surfaceContainerHigh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'onSurfaceVariant',
            mb: 2,
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 32 }}>
            shield
          </span>
        </Box>
        <Typography variant="headlineAgent" sx={{ color: 'onSurface', mb: 1 }}>
          No modifiers available
        </Typography>
        <Typography
          variant="bodyData"
          sx={{ color: 'onSurfaceVariant', maxWidth: 280, mx: 'auto', lineHeight: 1.4 }}
        >
          Row filters and column masks are only applicable to{' '}
          <Box component="span" sx={{ color: 'onSurface', fontWeight: 'bold' }}>
            TABLE
          </Box>{' '}
          or{' '}
          <Box component="span" sx={{ color: 'onSurface', fontWeight: 'bold' }}>
            COLUMN
          </Box>{' '}
          resources.
        </Typography>
      </Box>

      {/* Explanation Cards Stacked */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {/* Row Filter Card */}
        <Box
          sx={{
            bgcolor: 'surfaceContainer',
            borderLeft: '4px solid',
            borderLeftColor: 'warning.main',
            borderRadius: 1,
            p: 1.5,
            display: 'flex',
            gap: 2,
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ color: 'var(--mui-palette-warning-main)', marginTop: 2 }}
          >
            filter_list
          </span>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="bodyData" sx={{ fontWeight: 'bold', color: 'onSurface' }}>
                Row Filter
              </Typography>
              <Box
                sx={{
                  px: 1,
                  py: 0.25,
                  bgcolor: 'rgba(251, 191, 36, 0.1)',
                  color: 'warning.main',
                  border: 1,
                  borderColor: 'rgba(251, 191, 36, 0.2)',
                  borderRadius: 0.5,
                }}
              >
                <Typography variant="labelMono" sx={{ fontSize: 9 }}>
                  TABLE only
                </Typography>
              </Box>
            </Box>
            <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', fontSize: 13 }}>
              Restrict visibility to specific rows using SQL WHERE clauses. To use this, select a
              specific table instead of the whole database.
            </Typography>
          </Box>
        </Box>

        {/* Column Mask Card */}
        <Box
          sx={{
            bgcolor: 'surfaceContainer',
            borderLeft: '4px solid',
            borderLeftColor: 'outlineVariant',
            borderRadius: 1,
            p: 1.5,
            display: 'flex',
            gap: 2,
            opacity: 0.7,
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ color: 'var(--mui-palette-onSurfaceVariant)', marginTop: 2 }}
          >
            visibility_off
          </span>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Typography variant="bodyData" sx={{ fontWeight: 'bold', color: 'onSurface' }}>
                Column Mask
              </Typography>
              <Box
                sx={{
                  px: 1,
                  py: 0.25,
                  bgcolor: 'surfaceContainerHighest',
                  color: 'onSurfaceVariant',
                  border: 1,
                  borderColor: 'outlineVariant',
                  borderRadius: 0.5,
                }}
              >
                <Typography variant="labelMono" sx={{ fontSize: 9 }}>
                  COLUMN only
                </Typography>
              </Box>
            </Box>
            <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', fontSize: 13 }}>
              Anonymize sensitive data (PII) through hashing or redaction. To use this, navigate to
              a specific column.
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Scope Reminder Banner */}
      <Box
        sx={{
          bgcolor: 'rgba(var(--mui-palette-tertiary-mainChannel) / 0.1)',
          border: 1,
          borderColor: 'rgba(var(--mui-palette-tertiary-mainChannel) / 0.2)',
          borderRadius: 2,
          p: 1.5,
          display: 'flex',
          gap: 1.5,
          alignItems: 'flex-start',
        }}
      >
        <span
          className="material-symbols-outlined"
          style={{ color: 'var(--mui-palette-tertiary-main)', fontSize: 20, marginTop: 2 }}
        >
          info
        </span>
        <Typography variant="bodyData" sx={{ color: 'onTertiaryContainer', lineHeight: 1.4 }}>
          This permission will apply to{' '}
          <Box
            component="span"
            sx={{ fontFamily: 'var(--mui-fontFamily-label-mono)', color: 'tertiary.main' }}
          >
            {resourceName}
          </Box>{' '}
          and propagate to all{' '}
          <Box
            component="span"
            sx={{ fontFamily: 'var(--mui-fontFamily-label-mono)', fontWeight: 'bold' }}
          >
            12
          </Box>{' '}
          schemas,{' '}
          <Box
            component="span"
            sx={{ fontFamily: 'var(--mui-fontFamily-label-mono)', fontWeight: 'bold' }}
          >
            48
          </Box>{' '}
          tables, and{' '}
          <Box
            component="span"
            sx={{ fontFamily: 'var(--mui-fontFamily-label-mono)', fontWeight: 'bold' }}
          >
            210
          </Box>{' '}
          columns inside it...
        </Typography>
      </Box>

      {/* Quick Navigation */}
      {!lockResource && (
      <Box sx={{ pt: 2, borderTop: 1, borderColor: 'outlineVariant' }}>
        <Typography variant="caption" sx={{ color: 'onSurfaceVariant', display: 'block', mb: 1.5 }}>
          Need a modifier? Go to:
        </Typography>
        <Box sx={{ display: 'flex', gap: 1.5 }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => onGoToStep(0)}
            sx={{
              borderColor: 'outlineVariant',
              color: 'onSurface',
              textTransform: 'none',
              borderRadius: 4,
              px: 2,
              py: 0.75,
              fontSize: 13,
              '&:hover': { bgcolor: 'surfaceContainerHigh', borderColor: 'outline' },
            }}
          >
            Select a table →
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => onGoToStep(0)}
            sx={{
              borderColor: 'outlineVariant',
              color: 'onSurface',
              textTransform: 'none',
              borderRadius: 4,
              px: 2,
              py: 0.75,
              fontSize: 13,
              '&:hover': { bgcolor: 'surfaceContainerHigh', borderColor: 'outline' },
            }}
          >
            Select a column →
          </Button>
        </Box>
      </Box>
      )}

      {/* Step Completion Note */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', justifyContent: 'center', py: 1 }}>
        <span
          className="material-symbols-outlined"
          style={{ fontSize: 16, color: 'var(--mui-palette-onSurfaceVariant)' }}
        >
          check_circle
        </span>
        <Typography variant="caption" sx={{ color: 'onSurfaceVariant', fontStyle: 'italic' }}>
          This step is automatically complete — no modifier needed for database or schema resources.
        </Typography>
      </Box>
    </Box>
  )
}

export default NoModifierSection
