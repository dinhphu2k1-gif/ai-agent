import { Box, Button, Typography } from '@mui/material'
import type { ActionPromptData } from '../types'

interface ActionPromptCardProps {
  promptData: ActionPromptData
  onSelectOption: (optionId: string, optionLabel: string) => void
}

const ActionPromptCard = ({ promptData, onSelectOption }: ActionPromptCardProps) => {
  return (
    <Box
      sx={{
        mt: 'var(--mui-spacing-stack-md)',
        ml: 1,
        p: 2,
        bgcolor: 'surfaceContainerLow',
        borderRadius: 2,
        border: 1,
        borderColor: 'primary.main',
        boxShadow: 2,
        '@keyframes slideUp': {
          from: { opacity: 0, transform: 'translateY(16px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
        animation: 'slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
        <span
          className="material-symbols-outlined"
          style={{ color: 'var(--mui-palette-primary-main)', fontSize: 20 }}
        >
          pending_actions
        </span>
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
          {promptData.title}
        </Typography>
      </Box>

      <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant', mb: 2 }}>
        {promptData.description}
      </Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1.5 }}>
        {promptData.options.map((opt) => (
          <Button
            key={opt.actionId}
            onClick={() => onSelectOption(opt.actionId, opt.label)}
            sx={{
              bgcolor: 'primaryContainer',
              color: 'onPrimaryContainer',
              border: 1,
              borderRadius: 1,
              py: 1,
              px: 2,
              fontFamily: 'JetBrains Mono',
              fontSize: '12px',
              fontWeight: 500,
              textTransform: 'none',
              '&:hover': {
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
              },
            }}
          >
            {opt.label}
          </Button>
        ))}
      </Box>

      {promptData.customOptionLabel && (
        <Box sx={{ borderTop: 1, borderColor: 'outlineVariant', pt: 1.5, mt: 1 }}>
          <Box
            onClick={() => onSelectOption('custom', promptData.customOptionLabel || '')}
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              p: 1.5,
              bgcolor: 'surfaceContainerHighest',
              border: 1,
              borderColor: 'outlineVariant',
              borderRadius: 1,
              cursor: 'pointer',
              color: 'onSurfaceVariant',
              transition: 'all 0.15s ease-in-out',
              '&:hover': {
                bgcolor: 'surfaceBright',
                color: 'onSurface',
              },
              '&:hover .chevron': {
                transform: 'translateX(4px)',
              },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                edit_note
              </span>
              <Typography variant="bodyMain">{promptData.customOptionLabel}</Typography>
            </Box>
            <span
              className="material-symbols-outlined chevron"
              style={{ fontSize: 18, transition: 'transform 0.15s' }}
            >
              chevron_right
            </span>
          </Box>
        </Box>
      )}
    </Box>
  )
}

export default ActionPromptCard
