import '@mui/material/styles'

declare module '@mui/material/styles' {
  interface Palette {
    surface: string
    surfaceDim: string
    surfaceBright: string
    surfaceContainerLowest: string
    surfaceContainerLow: string
    surfaceContainer: string
    surfaceContainerHigh: string
    surfaceContainerHighest: string
    onSurface: string
    onSurfaceVariant: string
    inverseSurface: string
    inverseOnSurface: string
    outline: string
    outlineVariant: string
    surfaceTint: string

    // Custom flat colors matching MD3 design system from DESIGN.md
    onPrimary: string
    primaryContainer: string
    onPrimaryContainer: string
    inversePrimary: string

    onSecondary: string
    secondaryContainer: string
    onSecondaryContainer: string

    tertiary: string
    onTertiary: string
    tertiaryContainer: string
    onTertiaryContainer: string

    onError: string
    errorContainer: string
    onErrorContainer: string

    primaryFixed: string
    primaryFixedDim: string
    onPrimaryFixed: string
    onPrimaryFixedVariant: string

    secondaryFixed: string
    secondaryFixedDim: string
    onSecondaryFixed: string
    onSecondaryFixedVariant: string

    tertiaryFixed: string
    tertiaryFixedDim: string
    onTertiaryFixed: string
    onTertiaryFixedVariant: string

    // Custom Status/Role Colors
    statusActiveBg: string
    statusActiveText: string
    statusActiveBorder: string
    roleViewerBg: string
    roleViewerText: string
    roleViewerBorder: string
  }

  interface PaletteOptions {
    surface?: string
    surfaceDim?: string
    surfaceBright?: string
    surfaceContainerLowest?: string
    surfaceContainerLow?: string
    surfaceContainer?: string
    surfaceContainerHigh?: string
    surfaceContainerHighest?: string
    onSurface?: string
    onSurfaceVariant?: string
    inverseSurface?: string
    inverseOnSurface?: string
    outline?: string
    outlineVariant?: string
    surfaceTint?: string

    onPrimary?: string
    primaryContainer?: string
    onPrimaryContainer?: string
    inversePrimary?: string

    onSecondary?: string
    secondaryContainer?: string
    onSecondaryContainer?: string

    tertiary?: string
    onTertiary?: string
    tertiaryContainer?: string
    onTertiaryContainer?: string

    onError?: string
    errorContainer?: string
    onErrorContainer?: string

    primaryFixed?: string
    primaryFixedDim?: string
    onPrimaryFixed?: string
    onPrimaryFixedVariant?: string

    secondaryFixed?: string
    secondaryFixedDim?: string
    onSecondaryFixed?: string
    onSecondaryFixedVariant?: string

    tertiaryFixed?: string
    tertiaryFixedDim?: string
    onTertiaryFixed?: string
    onTertiaryFixedVariant?: string

    // Custom Status/Role Colors
    statusActiveBg?: string
    statusActiveText?: string
    statusActiveBorder?: string
    roleViewerBg?: string
    roleViewerText?: string
    roleViewerBorder?: string
  }

  interface TypographyVariants {
    displaySm: React.CSSProperties
    headlineAgent: React.CSSProperties
    bodyMain: React.CSSProperties
    bodyData: React.CSSProperties
    labelMono: React.CSSProperties
  }

  interface TypographyVariantsOptions {
    displaySm?: React.CSSProperties
    headlineAgent?: React.CSSProperties
    bodyMain?: React.CSSProperties
    bodyData?: React.CSSProperties
    labelMono?: React.CSSProperties
  }
}

declare module '@mui/material/Typography' {
  interface TypographyPropsVariantOverrides {
    displaySm: true
    headlineAgent: true
    bodyMain: true
    bodyData: true
    labelMono: true
  }
}
