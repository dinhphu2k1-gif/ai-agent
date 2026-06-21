import { MenuType } from '@/types/enum'
import type { IconMenu, Pages } from '@/types/type'
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord'
import {
  Collapse,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from '@mui/material'
import { IconChevronDown, IconChevronUp } from '@tabler/icons-react'
import { type ReactNode, useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'

// material-ui

// project imports
import NavItem from '../NavItem'

// assets

interface NavCollapseProp {
  menu: Pages
  level: number
  url: string
}

const NavCollapse = ({ menu, level, url }: NavCollapseProp): ReactNode => {
  const { pathname } = useLocation()

  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)

  const handleClick = (): void => {
    setOpen(!open)
    setSelected(!selected ? menu.id : null)
  }

  const checkOpenForParent = (child: Pages[], id: string): void => {
    child.forEach((item) => {
      if (pathname.includes(`${url}/${item.id}`)) {
        setOpen(true)
        setSelected(id)
      }
    })
  }

  // menu collapse for sub-levels
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSelected(null)
    if (menu.children) {
      menu.children.forEach((item) => {
        if (item.children?.length) {
          checkOpenForParent(item.children, menu.id)
        }
        if (pathname.includes(`${url}/${item.id}`)) {
          setSelected(menu.id)
          setOpen(true)
        }
      })
    }
    if (!pathname.includes(url) && open) {
      setOpen(false)
    }
    // eslint-disable-next-line
  }, [pathname, menu.children])

  // menu collapse & item
  const menus = menu.children?.map((item) => {
    switch (item.type) {
      case MenuType.Collapse:
        return <NavCollapse key={item.id} menu={item} level={level + 1} url={`${url}/${item.id}`} />
      case MenuType.Item:
        return <NavItem key={item.id} item={item} level={level + 1} url={`${url}/${item.id}`} />
      default:
        return (
          <Typography key={item.id} variant="h6" color="error" align="center">
            Menu Items Error
          </Typography>
        )
    }
  })

  const Icon = menu.icon as IconMenu
  const menuIcon = menu?.icon ? (
    <Icon strokeWidth={1.5} size="1.3rem" style={{ marginTop: 'auto', marginBottom: 'auto' }} />
  ) : (
    <FiberManualRecordIcon
      sx={{
        width: selected === menu.id ? 8 : 6,
        height: selected === menu.id ? 8 : 6,
      }}
      fontSize={level > 0 ? 'inherit' : 'medium'}
    />
  )

  return (
    <>
      <ListItemButton
        sx={{
          borderRadius: 1,
          mb: 0.5,
          alignItems: 'flex-start',
          backgroundColor: level > 1 ? 'transparent !important' : 'inherit',
          py: 0.75,
          pl: `${level * 10}px`,
          color: 'var(--mui-palette-onSurfaceVariant)',
          '&:hover': {
            bgcolor: 'var(--mui-palette-surfaceContainerHigh)',
            color: 'var(--mui-palette-onSurface)',
            '& .MuiListItemIcon-root': {
              color: 'var(--mui-palette-onSurface)',
            },
          },
          '&.Mui-selected': {
            bgcolor: 'color-mix(in srgb, var(--mui-palette-primary-main) 10%, transparent)',
            color: 'var(--mui-palette-primary-main)',
            '&:hover': {
              bgcolor: 'var(--mui-palette-surfaceContainerHigh)',
            },
            '& .MuiListItemIcon-root': {
              color: 'var(--mui-palette-primary-main)',
            },
            '& .MuiTypography-root': {
              fontWeight: 600,
            },
          },
        }}
        selected={selected === menu.id}
        onClick={handleClick}
      >
        <ListItemIcon sx={{ my: 'auto', minWidth: !menu.icon ? 18 : 36, color: 'inherit' }}>{menuIcon}</ListItemIcon>
        <ListItemText
          primary={
            <Typography
              variant={selected === menu.id ? 'h5' : 'body1'}
              color="inherit"
              sx={{ my: 'auto' }}
            >
              {menu.title}
            </Typography>
          }
          secondary={
            menu.caption && (
              <Typography variant="caption" gutterBottom>
                {menu.caption}
              </Typography>
            )
          }
        />
        {open ? (
          <IconChevronUp
            stroke={1.5}
            size="1rem"
            style={{ marginTop: 'auto', marginBottom: 'auto' }}
          />
        ) : (
          <IconChevronDown
            stroke={1.5}
            size="1rem"
            style={{ marginTop: 'auto', marginBottom: 'auto' }}
          />
        )}
      </ListItemButton>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <List
          component="div"
          disablePadding
          sx={{
            position: 'relative',
            // '&:after': {
            //   content: "''",
            //   position: 'absolute',
            //   left: 32,
            //   top: 0,
            //   height: '100%',
            //   width: '1px',
            //   opacity: 1,
            //   background: theme.palette.primary.light,
            // },
          }}
        >
          {menus}
        </List>
      </Collapse>
    </>
  )
}

export default NavCollapse
