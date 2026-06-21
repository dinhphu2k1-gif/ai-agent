import { Box, Typography } from '@mui/material'
import type { DataTable } from '@/api/chat'

interface DataResultTableProps {
  table: DataTable
}

const varianceColor = (value: string): string | undefined => {
  if (!value) return undefined
  const trimmed = value.trim()
  if (trimmed.startsWith('+')) return 'var(--mui-palette-primary-main)'
  if (trimmed.startsWith('-')) return 'var(--mui-palette-error-main)'
  return undefined
}

const DataResultTable = ({ table }: DataResultTableProps) => {
  const { title, columns, rows } = table

  if (columns.length === 0 || rows.length === 0) return null

  return (
    <Box
      sx={{
        mt: 'var(--mui-spacing-stack-md)',
        mb: 'var(--mui-spacing-stack-md)',
        bgcolor: 'background.default',
        borderRadius: 1,
        border: 1,
        borderColor: 'surfaceContainerHighest',
        overflow: 'hidden',
      }}
    >
      {title && (
        <Box
          sx={{
            bgcolor: 'surfaceContainerHighest',
            px: 1.5,
            py: 1,
            borderBottom: 1,
            borderColor: 'surfaceContainerHighest',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: 16, color: 'var(--mui-palette-onSurfaceVariant)' }}
          >
            table_chart
          </span>
          <Typography variant="labelMono" sx={{ color: 'onSurfaceVariant' }}>
            {title}
          </Typography>
        </Box>
      )}

      <Box sx={{ overflowX: 'auto' }}>
        <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <Box
            component="thead"
            sx={{
              bgcolor: 'surfaceContainerLow',
              color: 'onSurfaceVariant',
              borderBottom: 1,
              borderColor: 'surfaceContainerHighest',
            }}
          >
            <Box component="tr">
              {columns.map((col) => (
                <Box
                  key={col.key}
                  component="th"
                  sx={{
                    px: 2,
                    py: 1,
                    fontWeight: 500,
                    fontSize: '13px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {col.label}
                </Box>
              ))}
            </Box>
          </Box>
          <Box component="tbody">
            {rows.map((row, rowIdx) => (
              <Box
                component="tr"
                key={rowIdx}
                sx={{
                  borderBottom: rowIdx === rows.length - 1 ? 0 : 1,
                  borderColor: 'surfaceContainerHighest',
                  transition: 'background-color 0.15s',
                  '&:hover': {
                    bgcolor: 'surfaceContainerLow',
                  },
                }}
              >
                {columns.map((col) => {
                  const cell = row[col.key] ?? ''
                  const highlight = col.key === 'variance' ? varianceColor(cell) : undefined

                  return (
                    <Box
                      key={col.key}
                      component="td"
                      sx={{
                        px: 2,
                        py: 1,
                        fontSize: '13px',
                        color: highlight ?? 'onSurface',
                        fontWeight: highlight ? 500 : 400,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {cell}
                    </Box>
                  )
                })}
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </Box>
  )
}

export default DataResultTable
