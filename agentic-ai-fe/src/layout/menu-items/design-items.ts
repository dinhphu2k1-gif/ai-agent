import { MenuType } from '@/types/enum'
import type { Pages } from '@/types/type'
import {
  IconUser,
  IconUsers,
  IconShieldCheck,
  IconTerminal2,
  IconHistory,
} from '@tabler/icons-react'

const designItems: Pages[] = [
  {
    id: 'administration',
    title: 'Administration',
    type: MenuType.Group,
    children: [
      {
        id: 'users',
        title: 'Users',
        type: MenuType.Item,
        url: '/admin/users',
        icon: IconUser,
      },
      {
        id: 'groups',
        title: 'Groups',
        type: MenuType.Item,
        url: '/admin/groups',
        icon: IconUsers,
      },
      {
        id: 'roles',
        title: 'Roles',
        type: MenuType.Item,
        url: '/admin/roles',
        icon: IconShieldCheck,
      },
    ],
  },
  {
    id: 'logs-group',
    title: 'Activity',
    type: MenuType.Group,
    children: [
      {
        id: 'agent-logs',
        title: 'Agent Logs',
        type: MenuType.Item,
        url: '/logs/agents',
        icon: IconTerminal2,
      },
      {
        id: 'user-logs',
        title: 'User Logs',
        type: MenuType.Item,
        url: '/logs/users',
        icon: IconHistory,
      },
    ],
  },
]

export default designItems
