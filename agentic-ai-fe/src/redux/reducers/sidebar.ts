import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export interface SidebarState {
  isOpen: boolean
}

// init state for reducer
const initialState: SidebarState = {
  isOpen: true,
}

export const sidebarSlice = createSlice({
  name: 'sidebar',
  initialState,
  reducers: (create) => ({
    setOpen: create.reducer((state, action: PayloadAction<boolean>) => {
      state.isOpen = action.payload
    }),
  }),

  selectors: {
    selectSidebar: (counter) => counter.isOpen,
  },
})

// Action creators are generated for each case reducer function.
export const { setOpen } = sidebarSlice.actions

// Selectors returned by `slice.selectors` take the root state as their first argument.
export const { selectSidebar } = sidebarSlice.selectors
