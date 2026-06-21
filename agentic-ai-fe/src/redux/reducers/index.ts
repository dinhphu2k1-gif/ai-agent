import { combineSlices } from '@reduxjs/toolkit'
import { sidebarSlice } from './sidebar'
import { alertSlice } from './AlertSlice'
import { themeSlice } from './theme'

// `combineSlices` automatically combines the reducers using
// their `reducerPath`s, therefore we no longer need to call `combineReducers`.
export const rootReducer = combineSlices(
  sidebarSlice,
  alertSlice,
  themeSlice,
)
