import { CssBaseline } from '@mui/material'
import type { Theme as MuiTheme, ThemeOptions } from '@mui/material/styles'
import {
  ThemeProvider as MuiThemeProvider,
  StyledEngineProvider,
  createTheme,
  useColorScheme
} from '@mui/material/styles'
import { useEffect } from 'react'

import breakpoints from './breakpoints'
import { componentsOverrides } from './overide'
import { colorSchemes } from './palette'
import { createShadow } from './shadows'
import typography from './typography'
import { useAppSelector } from '@/redux/hooks'
import { selectThemeMode } from '@/redux/reducers/theme'

declare module '@mui/material/styles' {
  interface PaletteColor {
    lighter?: string
    200?: string
    darker?: string
  }
}

const ThemeSync = () => {
  const { setMode } = useColorScheme()
  const reduxMode = useAppSelector(selectThemeMode)

  useEffect(() => {
    if (setMode) {
      setMode(reduxMode)
    }
  }, [reduxMode, setMode])

  return null
}

const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const themeOptions: ThemeOptions = {
    colorSchemes,
    cssVariables: {
      colorSchemeSelector: 'data-mui-color-scheme',
    },
    typography,
    shape: { borderRadius: 4 },
    breakpoints,
    direction: 'ltr',
    shadows: createShadow(),
    components: componentsOverrides,
  }

  const theme: MuiTheme = createTheme(themeOptions)

  return (
    <StyledEngineProvider injectFirst>
      <MuiThemeProvider theme={theme}>
        <ThemeSync />
        <CssBaseline enableColorScheme />
        {children}
      </MuiThemeProvider>
    </StyledEngineProvider>
  )
}

export default ThemeProvider
