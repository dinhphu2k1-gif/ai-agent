import {
  Box,
  CircularProgress,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Typography,
} from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { IconHash } from '@tabler/icons-react'
import { useMemo, type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'

import type { Channel } from '@/api/chat'
import { useChatChannelsContext } from '@/pages/chat/context/ChatChannelsContext'

interface ChatChannelsNavProps {
  drawerOpen: boolean
  onRequestDelete: (channel: Channel) => void
}

const ChatChannelsNav = ({ drawerOpen, onRequestDelete }: ChatChannelsNavProps): ReactNode => {
  const theme = useTheme()
  const { pathname } = useLocation()
  const { channels, isLoading, error } = useChatChannelsContext()

  const grouped = useMemo(() => {
    const withCategory = channels.filter((ch) => ch.category)
    const withoutCategory = channels.filter((ch) => !ch.category)
    return { withCategory, withoutCategory, all: channels }
  }, [channels])

  if (!drawerOpen) return null

  if (isLoading && grouped.all.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
        <CircularProgress size={20} />
      </Box>
    )
  }

  if (error && grouped.all.length === 0) {
    return (
      <Typography variant="caption" sx={{ px: 2, py: 1, color: 'error.main', display: 'block' }}>
        {error}
      </Typography>
    )
  }

  const renderChannelItem = (channel: Channel) => {
    const href = `/chat/${channel.id}`
    const isSelected = pathname === href || pathname === `${href}/`

    return (
      <ListItemButton
        key={channel.id}
        component={Link}
        to={href}
        selected={isSelected}
        sx={{
          borderRadius: 1,
          mb: 0.25,
          py: 0.75,
          px: 1.5,
          pr: 0.5,
          color: theme.vars.palette.onSurfaceVariant,
          '&.Mui-selected': {
            bgcolor: 'color-mix(in srgb, var(--mui-palette-primary-main) 10%, transparent)',
            color: theme.vars.palette.primary.main,
          },
        }}
      >
        <ListItemIcon sx={{ minWidth: 28, color: 'inherit' }}>
          <IconHash stroke={1.5} size="1.2rem" />
        </ListItemIcon>
        <ListItemText
          primary={
            <Typography variant="bodyMain" color="inherit" noWrap>
              {channel.title}
            </Typography>
          }
        />
        <IconButton
          size="small"
          aria-label={`Delete ${channel.title}`}
          onClick={(event) => {
            event.preventDefault()
            event.stopPropagation()
            onRequestDelete(channel)
          }}
          sx={{
            color: 'var(--mui-palette-onSurfaceVariant)',
            '&:hover': { color: 'var(--mui-palette-error)' },
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
            delete
          </span>
        </IconButton>
      </ListItemButton>
    )
  }

  return (
    <List sx={{ px: 0 }}>
      <ListSubheader
        disableSticky
        sx={{
          ...theme.typography.labelMono,
          color: theme.vars.palette.onSurfaceVariant,
          bgcolor: 'transparent',
          px: 1.5,
          py: 1,
          lineHeight: 1,
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          fontSize: '10px',
        }}
      >
        Active Channels
      </ListSubheader>
      {grouped.withCategory.map(renderChannelItem)}
      {grouped.withoutCategory.map(renderChannelItem)}
      {grouped.all.length === 0 && !isLoading && (
        <Typography variant="caption" sx={{ px: 2, py: 1, color: 'onSurfaceVariant', display: 'block' }}>
          No channels yet. Create one to start chatting.
        </Typography>
      )}
    </List>
  )
}

export default ChatChannelsNav
