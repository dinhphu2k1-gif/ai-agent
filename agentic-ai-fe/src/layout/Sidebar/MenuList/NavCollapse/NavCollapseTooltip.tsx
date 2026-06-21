import { type ReactNode, useState } from 'react'

import NavItem from '../NavItem'
import NavCollapseClose from './NavCollapseClose'
import type { Pages } from '@/types/type'
import HtmlTooltip from '@/components/tooltip'

interface NavCollapseTooltipProp {
  menu: Pages
  level: number
  url: string
}

const NavCollapseTooltip = ({
  menu,
  level,
  url,
}: NavCollapseTooltipProp): ReactNode => {
  const [tooltipIsOpen, setTooltipIsOpen] = useState<boolean>(false)

  return (
    <HtmlTooltip
      open={tooltipIsOpen}
      onOpen={() => setTooltipIsOpen(true)}
      onClose={() => setTooltipIsOpen(false)}
      key={menu.id}
      placement={'right-start'}
      slotProps={{
        popper: {
          modifiers: [
            {
              name: 'offset',
              options: {
                offset: [0, -14],
              },
            },
          ],
        },
      }}
      title={
        <NavCollapseClose
          key={menu.id}
          menu={menu}
          level={level + 1}
          url={`${url}/${menu.id}`}
        />
      }
    >
      <div>
        <NavItem
          key={menu.id}
          item={menu}
          level={level + 1}
          url={`${url}/${menu.id}`}
          navClose
          isItemCollapse
          isOpenCollapse={tooltipIsOpen}
        />
      </div>
    </HtmlTooltip>
  )
}

export default NavCollapseTooltip
