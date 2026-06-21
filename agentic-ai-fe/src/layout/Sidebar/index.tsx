import { Box, Typography, useMediaQuery, Stack, IconButton, Button } from '@mui/material'
import MuiDrawer from '@mui/material/Drawer'
import { styled, useTheme, type Theme, type CSSObject } from '@mui/material/styles'
import {
  IconLayoutSidebarLeftCollapse,
  IconLayoutSidebarLeftExpand,
  IconPlus,
} from '@tabler/icons-react'

import { useRef, type ReactNode } from 'react'

// project imports
import MenuList from './MenuList'
import UserProfile from './UserProfile'
import ChatChannelsNav from './ChatChannelsNav'
import { useSidebarChatChannels } from './useSidebarChatChannels'
import CreateChannelDialog from '@/pages/chat/components/CreateChannelDialog'
import ConfirmDeleteChannelModal from '@/pages/chat/components/ConfirmDeleteChannelModal'
import { drawerWidth } from '@/types/constant'

// ==============================|| SIDEBAR DRAWER ||============================== //

const openedMixin = (theme: Theme): CSSObject => ({
  width: drawerWidth,
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
  overflowX: 'hidden',
  background: 'var(--mui-palette-surfaceContainerLow)',
  color: 'var(--mui-palette-onSurface)',
  borderRight: `1px solid var(--mui-palette-outlineVariant)`,
  [theme.breakpoints.up('md')]: {
    top: 0,
  },
})

const closedMixin = (theme: Theme): CSSObject => ({
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  overflowX: 'hidden',
  width: `calc(${theme.spacing(7)} + 1px)`,
  background: 'var(--mui-palette-surfaceContainerLow)',
  color: 'var(--mui-palette-onSurface)',
  borderRight: `1px solid var(--mui-palette-outlineVariant)`,
  [theme.breakpoints.up('sm')]: {
    width: `calc(${theme.spacing(9)} + 1px)`,
  },
  [theme.breakpoints.up('md')]: {
    top: 0,
  },
})

const Drawer = styled(MuiDrawer)(({ theme }) => ({
  width: drawerWidth,
  flexShrink: 0,
  whiteSpace: 'nowrap',
  boxSizing: 'border-box',
  variants: [
    {
      props: ({ open }): boolean => !!open,
      style: {
        ...openedMixin(theme),
        '& .MuiDrawer-paper': openedMixin(theme),
      },
    },
    {
      props: ({ open }): boolean => !open,
      style: {
        ...closedMixin(theme),
        '& .MuiDrawer-paper': closedMixin(theme),
      },
    },
  ],
}))

interface SidebarProps {
  drawerOpen: boolean
  drawerToggle: React.MouseEventHandler
}

const Sidebar = ({ drawerOpen, drawerToggle }: SidebarProps): ReactNode => {
  const theme = useTheme()
  const matchUpMd = useMediaQuery(theme.breakpoints.up('md'))

  const divRef = useRef<HTMLDivElement | null>(null)

  const {
    createOpen,
    setCreateOpen,
    deleteTarget,
    setDeleteTarget,
    isCreating,
    isDeleting,
    handleOpenCreate,
    handleCreateChannel,
    handleConfirmDelete,
  } = useSidebarChatChannels()

  const logoContent = (
    <Box
      sx={{
        display: 'flex',
        p: 2,
        alignItems: 'center',
        justifyContent: drawerOpen ? 'space-between' : 'center',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <img src={'/favicon.ico'} alt="" width={24} height={24} />
        {drawerOpen && (
          <Typography sx={{ ml: 1 }} variant="headlineAgent" color="primary.main">
            <span style={{ fontWeight: 600, letterSpacing: '0.05em' }}>Agritictial</span>
          </Typography>
        )}
      </Box>
      {matchUpMd && drawerOpen && (
        <IconButton
          onClick={drawerToggle}
          size="small"
          sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}
        >
          <IconLayoutSidebarLeftCollapse stroke={2} />
        </IconButton>
      )}
      {matchUpMd && !drawerOpen && (
        <Box sx={{ display: 'none' }} /> // Placeholder to keep spacing if needed
      )}
    </Box>
  )

  // If closed, the menu toggle button could be placed at the top instead of logo, but usually it's in the header.
  // We'll add it to the top for collapsed mode too.
  const collapsedLogoContent = (
    <Box
      sx={{
        display: 'flex',
        p: 2,
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <IconButton
        onClick={drawerToggle}
        size="small"
        sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}
      >
        <IconLayoutSidebarLeftExpand stroke={2} />
      </IconButton>
    </Box>
  )

  return (
    <Box
      component="nav"
      sx={{ flexShrink: { md: 0 }, width: matchUpMd ? (drawerOpen ? drawerWidth : 72) : 'auto' }}
      aria-label="sidebar navigation"
    >
      <Drawer
        variant={matchUpMd ? 'permanent' : 'temporary'}
        open={drawerOpen}
        anchor="left"
        onClose={drawerToggle}
        ModalProps={{ keepMounted: true }}
      >
        <Stack
          ref={divRef}
          sx={{
            height: '100%',
            overflow: 'hidden',
          }}
        >
          {drawerOpen ? logoContent : collapsedLogoContent}

          {/* New Chat Button */}
          <Box sx={{ px: drawerOpen ? 2 : 1.5, pb: 2, display: 'flex', justifyContent: 'center' }}>
            {drawerOpen ? (
              <Button
                variant="contained"
                fullWidth
                startIcon={<IconPlus size={18} />}
                sx={{ justifyContent: 'flex-start', borderRadius: 1 }}
                onClick={handleOpenCreate}
                disabled={isCreating}
              >
                New Chat
              </Button>
            ) : (
              <IconButton
                color="primary"
                aria-label="New chat channel"
                onClick={handleOpenCreate}
                disabled={isCreating}
                sx={{
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  borderRadius: 1,
                  '&:hover': { bgcolor: 'primary.dark' },
                }}
              >
                <IconPlus size={20} />
              </IconButton>
            )}
          </Box>

          <Box
            sx={{
              flexGrow: 1,
              overflowY: 'auto',
              overflowX: 'hidden',
              px: drawerOpen ? 2 : 1,
              '&::-webkit-scrollbar': { width: 4 },
              '&::-webkit-scrollbar-thumb': {
                borderRadius: 2,
                backgroundColor: '#888',
              },
            }}
          >
            <MenuList />
            <ChatChannelsNav drawerOpen={drawerOpen} onRequestDelete={setDeleteTarget} />
          </Box>
          <UserProfile drawerOpen={drawerOpen} />
        </Stack>
      </Drawer>

      <CreateChannelDialog
        open={createOpen}
        submitting={isCreating}
        onClose={() => setCreateOpen(false)}
        onCreate={handleCreateChannel}
      />

      <ConfirmDeleteChannelModal
        open={Boolean(deleteTarget)}
        channelTitle={deleteTarget?.title ?? ''}
        submitting={isDeleting}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  )
}

export default Sidebar
