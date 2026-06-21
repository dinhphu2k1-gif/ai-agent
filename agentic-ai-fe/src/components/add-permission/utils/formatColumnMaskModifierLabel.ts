import { MaskType } from '../types'

export const formatColumnMaskModifierLabel = (maskType: MaskType, maskPattern: string): string => {
  if (maskType === MaskType.Partial) {
    const pattern = maskPattern.trim()
    return pattern ? `${maskType}: ${pattern}` : maskType
  }
  return maskType
}
