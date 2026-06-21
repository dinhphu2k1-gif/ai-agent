import type { PaletteOptions } from '@mui/material/styles'

export const colorSchemes = {
  light: {
    palette: {
      mode: 'light',
      background: {
        default: '#faf8f6', // Warm cream
        paper: '#ffffff',
      },
      text: {
        primary: '#2c1a1c', // Deep warm brown
        secondary: '#5c4a4d', // Muted warm gray
        disabled: '#a0919a',
      },
      primary: {
        main: '#ae1c3f',
        contrastText: '#ffffff',
      },
      secondary: {
        main: '#4e5768',
        contrastText: '#ffffff',
      },
      error: {
        main: '#93000a',
        contrastText: '#ffffff',
      },
      success: {
        main: '#10b981', // emerald-500
        dark: '#059669', // emerald-600
        light: '#34d399', // emerald-400
        contrastText: '#ffffff',
      },
      divider: '#e2d9d6', // Warm divider

      // Custom MD3 Tokens for Light Mode — Warm Cream/Rose tones
      surface: '#faf8f6',
      surfaceDim: '#f0ece9', // Muted warm background
      surfaceBright: '#ffffff',
      surfaceContainerLowest: '#ffffff',
      surfaceContainerLow: '#f7f3f0', // Sidebar background — warm off-white
      surfaceContainer: '#f0ece9', // Card backgrounds
      surfaceContainerHigh: '#e8e0dc', // Selected items — warm rose hint
      surfaceContainerHighest: '#ddd5d1', // Hover states
      onSurface: '#2c1a1c',
      onSurfaceVariant: '#5c4a4d', // Secondary text
      inverseSurface: '#2c1a1c',
      inverseOnSurface: '#faf8f6',
      outline: '#a0919a', // Subtle warm gray borders
      outlineVariant: '#e2d9d6', // Light warm border
      surfaceTint: '#ae1c3f',

      onPrimary: '#ffffff',
      primaryContainer: '#ffdadc',
      onPrimaryContainer: '#40000f',
      inversePrimary: '#ffb2b9',

      onSecondary: '#ffffff',
      secondaryContainer: '#dce2f0',
      onSecondaryContainer: '#1a2233',

      tertiary: '#5b6b80',
      onTertiary: '#ffffff',
      tertiaryContainer: '#d8e5f8',
      onTertiaryContainer: '#142030',

      onError: '#ffffff',
      errorContainer: '#ffdad6',
      onErrorContainer: '#410002',

      primaryFixed: '#ffdadc',
      primaryFixedDim: '#ffb2b9',
      onPrimaryFixed: '#40000f',
      onPrimaryFixedVariant: '#91002e',

      secondaryFixed: '#dce2f0',
      secondaryFixedDim: '#c0c8d8',
      onSecondaryFixed: '#1a2233',
      onSecondaryFixedVariant: '#3c475a',

      tertiaryFixed: '#d8e5f8',
      tertiaryFixedDim: '#bccadd',
      onTertiaryFixed: '#142030',
      onTertiaryFixedVariant: '#3f4f64',

      // Custom Status/Role Colors for Light Mode
      statusActiveBg: '#d1fae5', // emerald-100
      statusActiveText: '#065f46', // emerald-800
      statusActiveBorder: '#a7f3d0', // emerald-200
      roleViewerBg: 'rgba(139, 92, 246, 0.2)', // violet-500 / 20
      roleViewerText: '#5b21b6', // violet-800
      roleViewerBorder: '#c4b5fd', // violet-300
    } as PaletteOptions,
  },
  dark: {
    palette: {
      mode: 'dark',
      background: {
        default: '#1d1011',
        paper: '#2a1c1d',
      },
      text: {
        primary: '#f6dcdd',
        secondary: '#e1bec0',
        disabled: '#a8898b',
      },
      primary: {
        main: '#ffb2b9',
        // main: '#ae1c3f',
        contrastText: '#67001e',
      },
      secondary: {
        main: '#bcc7de',
        contrastText: '#263143',
      },
      error: {
        main: '#ffb4ab',
        contrastText: '#690005',
      },
      success: {
        main: '#10b981', // emerald-500
        dark: '#059669', // emerald-600
        light: '#34d399', // emerald-400
        contrastText: '#ffffff',
      },
      divider: '#594042',

      // Custom MD3 Tokens for Dark Mode (From DESIGN.md)
      surface: '#1d1011',
      surfaceDim: '#1d1011',
      surfaceBright: '#463536',
      surfaceContainerLowest: '#170b0c',
      surfaceContainerLow: '#261819',
      surfaceContainer: '#2a1c1d',
      surfaceContainerHigh: '#352627',
      surfaceContainerHighest: '#413132',
      onSurface: '#f6dcdd',
      onSurfaceVariant: '#e1bec0',
      inverseSurface: '#f6dcdd',
      inverseOnSurface: '#3c2c2d',
      outline: '#a8898b',
      outlineVariant: '#594042',
      surfaceTint: '#ffb2b9',

      onPrimary: '#67001e',
      primaryContainer: '#ae1c3f',
      onPrimaryContainer: '#ffc2c7',
      inversePrimary: '#b42243',

      onSecondary: '#263143',
      secondaryContainer: '#3e495d',
      onSecondaryContainer: '#aeb9d0',

      tertiary: '#b7c8e1',
      onTertiary: '#213145',
      tertiaryContainer: '#4b5b71',
      onTertiaryContainer: '#c2d3ed',

      onError: '#690005',
      errorContainer: '#93000a',
      onErrorContainer: '#ffdad6',

      primaryFixed: '#ffdadc',
      primaryFixedDim: '#ffb2b9',
      onPrimaryFixed: '#40000f',
      onPrimaryFixedVariant: '#91002e',

      secondaryFixed: '#d8e3fb',
      secondaryFixedDim: '#bcc7de',
      onSecondaryFixed: '#111c2d',
      onSecondaryFixedVariant: '#3c475a',

      tertiaryFixed: '#d3e4fe',
      tertiaryFixedDim: '#b7c8e1',
      onTertiaryFixed: '#0b1c30',
      onTertiaryFixedVariant: '#38485d',

      // Custom Status/Role Colors for Dark Mode
      statusActiveBg: '#064e3b',
      statusActiveText: '#34d399',
      statusActiveBorder: '#047857',
      roleViewerBg: 'rgba(76, 29, 149, 0.3)', // #4c1d95 / 30
      roleViewerText: '#c4b5fd',
      roleViewerBorder: '#5b21b6',
    } as PaletteOptions,
  },
}
