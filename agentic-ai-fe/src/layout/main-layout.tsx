import { Box } from '@mui/material'
import { styled } from '@mui/material/styles'

// redux
import type { ReactNode } from 'react'
import { Outlet } from 'react-router-dom'

// assets
import Sidebar from './Sidebar'
import { ChatChannelsProvider } from '@/pages/chat/context/ChatChannelsContext'
import { drawerWidth } from '@/types/constant'
import { useAppSelector, useAppDispatch } from '@/redux/hooks'
import { selectSidebar, setOpen } from '@/redux/reducers/sidebar'

// styles
const Main = styled('main', {
  shouldForwardProp: (prop: string) => prop !== 'open',
})<{
  open?: boolean
}>(({ theme, open }) => ({
  width: '100%',
  minHeight: '100vh',
  flexGrow: 1,
  backgroundColor: 'var(--mui-palette-background-default)',
  transition: theme.transitions.create(
    'margin',
    open
      ? {
          easing: theme.transitions.easing.easeOut,
          duration: theme.transitions.duration.enteringScreen,
        }
      : {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.leavingScreen,
        }
  ),
  [theme.breakpoints.up('md')]: {
    width: open ? `calc(100% - ${drawerWidth}px)` : 'calc(100% - 72px)',
  },
}))

// ==============================|| MAIN LAYOUT ||============================== //

const MainLayout = (): ReactNode => {
  const leftDrawerOpened: boolean = useAppSelector(selectSidebar)
  const dispatch = useAppDispatch()

  const handleLeftDrawerToggle = (): void => {
    dispatch(setOpen(!leftDrawerOpened))
  }

  return (
    <ChatChannelsProvider>
      <Box sx={{ display: 'flex', bgcolor: 'var(--mui-palette-background-paper)' }}>
        <Sidebar drawerOpen={leftDrawerOpened} drawerToggle={handleLeftDrawerToggle} />
        <Main open={leftDrawerOpened}>
          <Outlet />
        </Main>
      </Box>
    </ChatChannelsProvider>
  )
}

export default MainLayout
