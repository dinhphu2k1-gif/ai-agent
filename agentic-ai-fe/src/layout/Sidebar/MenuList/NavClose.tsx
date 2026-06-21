import { List, ListItem, ListItemButton, ListItemIcon, useTheme } from '@mui/material'
import { type ReactNode, forwardRef } from 'react'
import { Link, useLocation } from 'react-router-dom'

// material-ui

// project imports
import NavCollapseClose from './NavCollapse/NavCollapseClose'
import { MenuType } from '@/types/enum'
import menuItems from '@/layout/menu-items'
import HtmlTooltip from '@/components/tooltip'
import type { IconMenu } from '@/types/type'

// ==============================|| SIDEBAR MENU LIST GROUP ||============================== //

const NavClose = (): ReactNode => {
  const { pathname } = useLocation()
  const theme = useTheme()

  const items = menuItems.items.map((item) =>
    item.children?.map((menu) => {
      const Icon = menu.icon as IconMenu

      const menuIcon = (
        <Icon
          strokeWidth={2}
          size="1rem"
          style={{
            width: 20,
            height: 20,
          }}
        />
      )

      const listItemProps = {
        component:
          menu.type === MenuType.Item
            ? forwardRef<HTMLAnchorElement>((props, ref) => (
                <Link
                  ref={ref}
                  {...props}
                  to={menu.url || `${item.id}/${menu.id}` || ''}
                  target={menu.target ? '_blank' : '_self'}
                />
              ))
            : undefined,
      }

      const itemBtn = (
        <ListItemButton
          {...listItemProps}
          selected={pathname.includes(menu.url || `${item.id}/${menu.id}`)}
          sx={{
            mt: 0.5,
            px: 2.75,
            py: 1.25,
            justifyContent: 'center',
            borderRadius: 1,
            '&.Mui-selected': {
              bgcolor: 'color-mix(in srgb, var(--mui-palette-primary-main) 10%, transparent)',
              color: theme.vars.palette.primary.main,
              '&:hover': {
                bgcolor: theme.vars.palette.surfaceContainerHigh,
              },
              '& .MuiListItemIcon-root': {
                color: theme.vars.palette.primary.main,
              },
            },
            '&:hover': {
              bgcolor: theme.vars.palette.surfaceContainerHigh,
              color: theme.vars.palette.onSurface,
              '& .MuiListItemIcon-root': {
                color: theme.vars.palette.onSurface,
              },
            },
          }}
        >
          <ListItemIcon
            sx={{
              minWidth: 0,
              justifyContent: 'center',
              mr: 'auto',
              color: 'var(--mui-palette-onSurfaceVariant)',
            }}
          >
            {menuIcon}
          </ListItemIcon>
        </ListItemButton>
      )

      return (
        <ListItem key={menu.id} disablePadding sx={{ display: 'block', width: 42 }}>
          <HtmlTooltip
            placement={'right-start'}
            title={
              menu.type === MenuType.Item ? null : (
                <NavCollapseClose level={1} menu={menu} url={`/${item.id}/${menu.id}`} />
              )
            }
          >
            {itemBtn}
          </HtmlTooltip>
        </ListItem>
      )
    })
  )

  return (
    <List
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      {items}
    </List>
  )
}

export default NavClose
