// project imports
import type { ReactNode } from 'react'

import NavClose from './NavClose'
import NavOpen from './NavOpen'
import { useAppSelector } from '@/redux/hooks'
import { selectSidebar } from '@/redux/reducers/sidebar'

// ==============================|| SIDEBAR MENU LIST ||============================== //

const MenuList = (): ReactNode => {
  const leftDrawerOpened: boolean = useAppSelector(selectSidebar)

  return leftDrawerOpened ? <NavOpen /> : <NavClose />
}

export default MenuList
