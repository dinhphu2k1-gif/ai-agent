import { Box } from '@mui/material'
import { MaskType } from '../../../types'

export const renderMaskedValue = (val: string, maskType: MaskType, maskPattern: string) => {
  if (maskType === MaskType.Full) {
    return (
      <Box component="span" sx={{ color: 'error.main' }}>
        ***
      </Box>
    )
  }
  if (maskType === MaskType.Hash) {
    return (
      <Box component="span" sx={{ opacity: 0.7, fontSize: 11 }}>
        e3b0c442...
      </Box>
    )
  }
  if (maskType === MaskType.Nullify) {
    return (
      <Box component="span" sx={{ fontStyle: 'italic', opacity: 0.5 }}>
        NULL
      </Box>
    )
  }
  return (
    <Box component="span">
      {val.split('').map((char, idx) => {
        const patChar = maskPattern[idx]
        const isMasked = patChar === 'X' || patChar === 'x'
        if (isMasked) {
          return (
            <Box key={idx} component="span" sx={{ color: 'error.main' }}>
              *
            </Box>
          )
        }
        return <span key={idx}>{patChar !== undefined ? patChar : char}</span>
      })}
    </Box>
  )
}
