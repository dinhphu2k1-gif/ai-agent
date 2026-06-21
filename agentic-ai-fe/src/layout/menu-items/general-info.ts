// assets
import { IconApps, IconBrandAuth0, IconUsers } from '@tabler/icons-react'
import { MenuType } from '@/types/enum'
import type { Pages } from '@/types/type'

// constant
const icons = {
  IconApps,
  IconUsers,
  IconBrandAuth0,
}

const generalInfo: Pages = {
  id: 'general-info',
  title: 'Thông tin chung',
  type: MenuType.Group,
  children: [
    {
      id: 'applications',
      title: 'Ứng dụng',
      type: MenuType.Item,
      icon: icons.IconApps,
    },
    {
      id: 'users',
      title: 'Người dùng',
      type: MenuType.Item,
      icon: icons.IconUsers,
    },
    {
      id: 'group-user',
      title: 'Nhóm người dùng',
      type: MenuType.Collapse,
      icon: icons.IconBrandAuth0,
      children: [
        {
          id: 'screen',
          title: 'Màn hình',
          type: MenuType.Item,
        },
        {
          id: 'feature',
          title: 'Tính năng',
          type: MenuType.Item,
        },
        {
          id: 'author',
          title: 'Phân quyền',
          type: MenuType.Item,
        },
      ],
    },
  ],
}

export default generalInfo
