interface rpvFontSizes {
  sm: number
  md: number
  lg: number
}

interface cssFontSizes {
  '@media (min-width:600px)': { fontSize: string }
  '@media (min-width:900px)': { fontSize: string }
  '@media (min-width:1200px)': { fontSize: string }
}

export function remToPx(value: string): number {
  return Math.round(parseFloat(value) * 16)
}

export function pxToRem(value: number): string {
  return `${value / 16}rem`
}

export function responsiveFontSizes({
  sm,
  md,
  lg,
}: rpvFontSizes): cssFontSizes {
  return {
    '@media (min-width:600px)': {
      fontSize: pxToRem(sm),
    },
    '@media (min-width:900px)': {
      fontSize: pxToRem(md),
    },
    '@media (min-width:1200px)': {
      fontSize: pxToRem(lg),
    },
  }
}
