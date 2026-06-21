import { ResourceType } from './types'
import type { ResourceNode, PermissionAction } from './types'

export const MOCK_RESOURCES: ResourceNode[] = [
  {
    id: 'db1',
    name: 'analytics_db',
    type: ResourceType.Database,
    children: [
      {
        id: 'sch1',
        name: 'public',
        type: ResourceType.Schema,
        children: [
          {
            id: 'tbl1',
            name: 'users',
            type: ResourceType.Table,
            children: [
              { id: 'col1', name: 'id', type: ResourceType.Column, isPrimaryKey: true },
              { id: 'col2', name: 'email', type: ResourceType.Column },
              { id: 'col3', name: 'created_at', type: ResourceType.Column },
            ],
          },
          {
            id: 'tbl2',
            name: 'events',
            type: ResourceType.Table,
            children: [
              { id: 'col4', name: 'event_id', type: ResourceType.Column, isPrimaryKey: true },
              { id: 'col5', name: 'event_type', type: ResourceType.Column },
              { id: 'col6', name: 'user_id', type: ResourceType.Column, isForeignKey: true },
            ],
          },
        ],
      },
      {
        id: 'sch2',
        name: 'internal',
        type: ResourceType.Schema,
        children: [{ id: 'tbl3', name: 'audit_logs', type: ResourceType.Table }],
      },
    ],
  },
  {
    id: 'db2',
    name: 'marketing_db',
    type: ResourceType.Database,
    children: [
      {
        id: 'sch3',
        name: 'campaigns',
        type: ResourceType.Schema,
        children: [{ id: 'tbl4', name: 'ads_performance', type: ResourceType.Table }],
      },
    ],
  },
]

export const TYPE_ICONS: Record<ResourceType, { icon: string; color: string }> = {
  [ResourceType.Database]: { icon: 'database', color: 'var(--mui-palette-secondary-main)' },
  [ResourceType.Schema]: { icon: 'folder', color: 'var(--mui-palette-tertiary)' },
  [ResourceType.Table]: { icon: 'table_view', color: 'var(--mui-palette-onSecondaryContainer)' },
  [ResourceType.Column]: { icon: 'view_column', color: 'var(--mui-palette-onSurfaceVariant)' },
}

export const AVAILABLE_ACTIONS: PermissionAction[] = [
  { name: 'SELECT', description: 'Read rows', icon: 'visibility' },
  { name: 'DESCRIBE', description: 'View structure', icon: 'info' },
]

export const STEPS = ['Resource', 'Actions & Effect', 'Modifier', 'Review']
