import { MenuType } from '@/types/enum'
import type { Pages } from '@/types/type'
import { List, Typography } from '@mui/material'

import type { ReactNode } from 'react'

import NavItem from '../NavItem'
import NavCollapseTooltip from './NavCollapseTooltip'

interface NavCollapseCloseProp {
  menu: Pages
  level: number
  url: string
}

const NavCollapseClose = ({
  menu,
  level,
  url,
}: NavCollapseCloseProp): ReactNode => {
  // menu collapse & item
  const menus = menu.children?.map((item: Pages) => {
    switch (item.type) {
      case MenuType.Collapse:
        return (
          <NavCollapseTooltip
            key={item.id}
            level={level}
            menu={item}
            url={url}
          />
        )
      case MenuType.Item:
        return (
          <NavItem
            key={item.id}
            item={item}
            level={level + 1}
            url={`${url}/${item.id}`}
            navClose
          />
        )
      default:
        return (
          <Typography key={item.id} variant="h6" color="error" align="center">
            Menu Items Error
          </Typography>
        )
    }
  })

  return (
    <List component="div" disablePadding sx={{ position: 'relative' }}>
      {menus}
    </List>
  )
}

export default NavCollapseClose
