import { pxToRem } from '@/utils/getFontValue'
import type { TypographyVariantsOptions } from '@mui/material/styles'
const FONT_PRIMARY: string = "'Inter', sans-serif"
const FONT_MONO: string = "'JetBrains Mono', monospace"

const typography: TypographyVariantsOptions = {
  fontFamily: FONT_PRIMARY,
  fontWeightRegular: 400,
  fontWeightMedium: 500,
  fontWeightBold: 600,

  displaySm: {
    fontFamily: FONT_PRIMARY,
    fontSize: '24px',
    fontWeight: 600,
    lineHeight: '32px',
    letterSpacing: '-0.02em',
  },
  headlineAgent: {
    fontFamily: FONT_PRIMARY,
    fontSize: '16px',
    fontWeight: 600,
    lineHeight: '24px',
    letterSpacing: '-0.01em',
  },
  bodyMain: {
    fontFamily: FONT_PRIMARY,
    fontSize: '14px',
    fontWeight: 400,
    lineHeight: '20px',
    letterSpacing: '0em',
  },
  bodyData: {
    fontFamily: FONT_PRIMARY,
    fontSize: '13px',
    fontWeight: 400,
    lineHeight: '18px',
    letterSpacing: '0em',
  },
  labelMono: {
    fontFamily: FONT_MONO,
    fontSize: '12px',
    fontWeight: 500,
    lineHeight: '16px',
    letterSpacing: '0.02em',
  },
  caption: {
    fontFamily: FONT_PRIMARY,
    fontSize: '12px',
    fontWeight: 400,
    lineHeight: '16px',
    letterSpacing: '0em',
  },

  // Standard overrides to map roughly to our design where appropriate
  h1: {
    fontFamily: FONT_PRIMARY,
    fontWeight: 600,
    fontSize: pxToRem(32),
  },
  h2: {
    fontFamily: FONT_PRIMARY,
    fontWeight: 600,
    fontSize: pxToRem(24),
  },
  h3: {
    fontFamily: FONT_PRIMARY,
    fontWeight: 600,
    fontSize: pxToRem(20),
  },
  h4: {
    fontFamily: FONT_PRIMARY,
    fontWeight: 600,
    fontSize: pxToRem(18),
  },
  h5: {
    fontFamily: FONT_PRIMARY,
    fontWeight: 600,
    fontSize: pxToRem(16),
  },
  h6: {
    fontFamily: FONT_PRIMARY,
    fontWeight: 600,
    fontSize: pxToRem(14),
  },
  body1: {
    fontFamily: FONT_PRIMARY,
    fontSize: '14px',
    fontWeight: 400,
    lineHeight: '20px',
  },
  body2: {
    fontFamily: FONT_PRIMARY,
    fontSize: '13px',
    fontWeight: 400,
    lineHeight: '18px',
  },
  button: {
    fontFamily: FONT_PRIMARY,
    fontWeight: 600,
    fontSize: '14px',
    textTransform: 'none',
  },
}

export default typography
