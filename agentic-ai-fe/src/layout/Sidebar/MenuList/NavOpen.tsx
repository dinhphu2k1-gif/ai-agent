// material-ui
import { Typography } from '@mui/material'
import type { ReactNode } from 'react'

// project imports
import NavGroup from './NavGroup'
import menuItems from '@/layout/menu-items'
import { MenuType } from '@/types/enum'

// ==============================|| SIDEBAR MENU LIST ||============================== //

const NavOpen = (): ReactNode => {
  const navItems = menuItems.items.map((item) => {
    switch (item.type) {
      case MenuType.Group:
        return <NavGroup key={item.id} item={item} />
      default:
        return (
          <Typography key={item.id} variant="h6" color="error" align="center">
            Menu Items Error
          </Typography>
        )
    }
  })

  return <>{navItems}</>
}

export default NavOpen
