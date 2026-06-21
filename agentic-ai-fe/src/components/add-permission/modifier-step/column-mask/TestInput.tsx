import { Box, Typography, TextField } from '@mui/material'
import { MaskType } from '../../types'
import { renderMaskedValue } from './maskUtils'

interface TestInputProps {
  testValue: string
  onChangeTestValue: (value: string) => void
  maskType: MaskType
  maskPattern: string
}

const TestInput = ({ testValue, onChangeTestValue, maskType, maskPattern }: TestInputProps) => {
  return (
    <Box sx={{ mt: 1, pt: 2, borderTop: 1, borderColor: 'outlineVariant' }}>
      <Typography variant="caption" sx={{ color: 'onSurfaceVariant', display: 'block', mb: 1 }}>
        Test your own value:
      </Typography>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          size="small"
          value={testValue}
          onChange={(e) => onChangeTestValue(e.target.value)}
          placeholder="e.g. 091-555-8888"
          sx={{
            flex: 1,
            '& .MuiOutlinedInput-root': {
              bgcolor: 'surfaceContainer',
              borderRadius: 1,
              color: 'onSurface',
            },
          }}
        />
      </Box>
      {testValue && (
        <Box
          sx={{
            mt: 1.5,
            p: 1.25,
            bgcolor: 'surfaceContainerLow',
            borderRadius: 1,
            border: 1,
            borderColor: 'outlineVariant',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
            Result:
          </Typography>
          <Typography variant="labelMono" sx={{ color: 'onSurface', fontWeight: 'bold' }}>
            {renderMaskedValue(testValue, maskType, maskPattern)}
          </Typography>
        </Box>
      )}
    </Box>
  )
}

export default TestInput
