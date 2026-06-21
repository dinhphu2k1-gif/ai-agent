// assets
import { IconBrandTeams, IconDoor } from '@tabler/icons-react'
import { MenuType } from '@/types/enum'
import type { Pages } from '@/types/type'

// constant
const icons = {
  IconDoor,
  IconBrandTeams,
}

const generalData: Pages = {
  id: 'general-data',
  title: 'Dữ liệu chung',
  type: MenuType.Group,
  children: [
    {
      id: 'deparment',
      title: 'Phòng ban',
      type: MenuType.Item,
      icon: icons.IconDoor,
    },
    {
      id: 'branch',
      title: 'Chi nhánh',
      type: MenuType.Item,
      icon: icons.IconBrandTeams,
    },
  ],
}

export default generalData
