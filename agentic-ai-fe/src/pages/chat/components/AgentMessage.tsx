import { useMemo } from 'react'
import { Box, Button, Typography } from '@mui/material'
import type { AgentMessageData } from '../types'
import { normalizeAgentData } from '../helpers/normalizeAgentData'
import DataResultTable from './DataResultTable'
import SqlQueryBlock from './SqlQueryBlock'

interface AgentMessageProps {
  agentData: AgentMessageData
  onActionClick?: (actionId: string, label: string) => void
}

const AgentMessage = ({ agentData, onActionClick }: AgentMessageProps) => {
  const normalized = useMemo(() => normalizeAgentData(agentData), [agentData])
  const { executionTrace, paragraphs, sqlQuery, dataTable, actionButtons } = normalized

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignSelf: 'flex-start',
        width: '100%',
        maxWidth: 'var(--mui-spacing-chat-max-width)',
        position: 'relative',
        '@keyframes slideIn': {
          from: { opacity: 0, transform: 'translateX(-12px)' },
          to: { opacity: 1, transform: 'translateX(0)' },
        },
        animation: 'slideIn 0.3s ease-out forwards',
      }}
    >
      <Box
        sx={{
          bgcolor: 'surfaceContainer',
          px: 2,
          py: 1.75,
          borderRadius: 2,
          border: 1,
          borderColor: 'surfaceContainerHigh',
          color: 'onSurface',
          ml: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}
      >
        {executionTrace && executionTrace.length > 0 && (
          <Box
            component="details"
            sx={{
              mb: 'var(--mui-spacing-stack-sm)',
              border: 1,
              borderRadius: 1,
              borderColor: 'outlineVariant',
              bgcolor: 'surfaceContainerLow',
              overflow: 'hidden',
              '&[open] summary span.chevron': {
                transform: 'rotate(90deg)',
              },
            }}
          >
            <Box
              component="summary"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                p: 1,
                fontFamily: 'JetBrains Mono',
                fontSize: '12px',
                color: 'onSurfaceVariant',
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: 'surfaceContainerHighest',
                },
                listStyle: 'none',
                '&::-webkit-details-marker': {
                  display: 'none',
                },
              }}
            >
              <span
                className="material-symbols-outlined chevron"
                style={{ fontSize: 16, transition: 'transform 0.15s' }}
              >
                chevron_right
              </span>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  memory
                </span>
                Execution Trace
              </Box>
            </Box>

            <Box
              sx={{
                p: 1.5,
                borderTop: 1,
                display: 'flex',
                flexDirection: 'column',
                borderColor: 'outlineVariant',
                gap: 2,
                bgcolor: 'surfaceContainerLowest',
              }}
            >
              {executionTrace.map((step, idx) => (
                <Box key={idx} sx={{ display: 'flex', alignItems: 'start', gap: 1 }}>
                  <span
                    className="material-symbols-outlined"
                    style={{ fontSize: 16, color: 'var(--mui-palette-primary-main)', marginTop: 2 }}
                  >
                    {step.icon}
                  </span>
                  <Box>
                    <Typography
                      variant="bodyData"
                      sx={{ fontWeight: 500, color: 'onSurface', display: 'block' }}
                    >
                      {step.title}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{ color: 'onSurfaceVariant', mt: 0.25, display: 'block' }}
                    >
                      {step.description}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        )}

        {sqlQuery && <SqlQueryBlock sql={sqlQuery} />}

        {paragraphs.map((p, idx) => (
          <Typography
            key={idx}
            variant="bodyMain"
            sx={{
              lineHeight: 1.6,
              mb: idx === paragraphs.length - 1 && !dataTable ? 0 : 1.5,
              whiteSpace: 'pre-wrap',
            }}
          >
            {p}
          </Typography>
        ))}

        {dataTable && <DataResultTable table={dataTable} />}

        {actionButtons && actionButtons.length > 0 && (
          <Box
            sx={{ mt: 'var(--mui-spacing-stack-sm)', display: 'flex', gap: 1, flexWrap: 'wrap' }}
          >
            {actionButtons.map((btn, idx) => (
              <Button
                key={idx}
                onClick={() => onActionClick && onActionClick(btn.actionId, btn.label)}
                sx={{
                  bgcolor: 'surfaceContainerHighest',
                  color: 'onSurface',
                  border: 1,
                  borderColor: 'outlineVariant',
                  borderRadius: 1,
                  py: 0.75,
                  px: 1.5,
                  fontFamily: 'JetBrains Mono',
                  fontSize: '11px',
                  textTransform: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                  transition: 'background-color 0.15s',
                  '&:hover': {
                    bgcolor: 'surfaceBright',
                  },
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                  {btn.icon}
                </span>
                {btn.label}
              </Button>
            ))}
          </Box>
        )}
      </Box>
    </Box>
  )
}

export default AgentMessage
