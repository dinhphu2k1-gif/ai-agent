import { Box, Typography, Switch } from '@mui/material'
import { MaskType } from '../../../types'
import MaskTypeSelector from './MaskTypeSelector'
import PatternInput from './PatternInput'
import CharacterMap from './CharacterMap'
import MaskPreview from './MaskPreview'
import TestInput from './TestInput'

interface ColumnMaskSectionProps {
  columnMaskEnabled: boolean
  onChangeColumnMaskEnabled: (enabled: boolean) => void
  maskType: MaskType
  onChangeMaskType: (type: MaskType) => void
  maskPattern: string
  onChangeMaskPattern: (pattern: string) => void
  testValue: string
  onChangeTestValue: (value: string) => void
}

const ColumnMaskSection = ({
  columnMaskEnabled,
  onChangeColumnMaskEnabled,
  maskType,
  onChangeMaskType,
  maskPattern,
  onChangeMaskPattern,
  testValue,
  onChangeTestValue,
}: ColumnMaskSectionProps) => {
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
            Add column mask
          </Typography>
          <Typography variant="caption" sx={{ color: 'onSurfaceVariant' }}>
            Obscure sensitive data in query results
          </Typography>
        </Box>
        <Switch
          checked={columnMaskEnabled}
          onChange={(e) => onChangeColumnMaskEnabled(e.target.checked)}
          color="primary"
        />
      </Box>

      {columnMaskEnabled && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <MaskTypeSelector maskType={maskType} onChangeMaskType={onChangeMaskType} />

          {maskType === MaskType.Partial && (
            <PatternInput maskPattern={maskPattern} onChangeMaskPattern={onChangeMaskPattern} />
          )}

          {maskType === MaskType.Partial && maskPattern && (
            <CharacterMap maskPattern={maskPattern} />
          )}

          <MaskPreview maskType={maskType} maskPattern={maskPattern} />

          <TestInput
            testValue={testValue}
            onChangeTestValue={onChangeTestValue}
            maskType={maskType}
            maskPattern={maskPattern}
          />
        </Box>
      )}
    </Box>
  )
}

export default ColumnMaskSection
