import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export type ThemeMode = 'light' | 'dark' | 'system'

export interface ThemeState {
  mode: ThemeMode
}

const initialState: ThemeState = {
  mode: 'system',
}

export const themeSlice = createSlice({
  name: 'theme',
  initialState,
  reducers: (create) => ({
    setThemeMode: create.reducer((state, action: PayloadAction<ThemeMode>) => {
      state.mode = action.payload
    }),
  }),
  selectors: {
    selectThemeMode: (state) => state.mode,
  },
})

export const { setThemeMode } = themeSlice.actions
export const { selectThemeMode } = themeSlice.selectors
