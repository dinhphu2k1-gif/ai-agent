import type { AssignableGroup, AssignableUser, Permission, Role, RoleActors } from './types'

export const AVAILABLE_USERS_CATALOG: AssignableUser[] = [
  {
    id: 'catalog-u1',
    name: 'Eleanor Vance',
    email: 'e.vance@corp.com',
    isOnline: true,
    avatarUrl:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuBd8gf5vXlKpv1cYWZU6mEi4Tiy2WyQi84QkiZA6lug3pgq4umeopqc5L19yaSiLSLSKkE3bsYQClLHRG9g-vI9VCoWIH_EUsfPcchKMbGOvch4Y2d0upivpJMefV5Fx1GqtmqjTwdjo-ARNQUoamwXsj732AWMDTpEKwsoS35pAFJ61Ja7LpnHW72EpdKNvJDRNDJidVLb8gXMciufYX8RcwP_fOhamtioEPZuEJLvMDR0QEv2txVaME7gafQs2n4ZzP5EgXKQLHkY',
  },
  {
    id: 'catalog-u2',
    name: 'Julian Montague',
    email: 'j.montague@corp.com',
    isOnline: false,
    avatarUrl:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuD2zhXNNYCMxBS6ue-kegcv3lfpfsCKaiMnihnTDFD_bp9So9zMyKYUL9pJmFjcSBBV68uGvD6T4BbloYRsjixMmOwiwxN2FvgVqNZF3iDf20iJp7w8pDP_EXbuRQnhjT6UVpGKvB0k7c6GcYvun1XJ7npF1bqaiKDwK6mr38IFhQEXRDr6QMDIP8FKEXYrkSsYhVeNwByFbRGnTW145aCTYqMDaAHzT8awEKZKfkK8SjAL2qmqqgF8NDL2loSr1uc-UchdCIwbFxkL',
  },
  {
    id: 'catalog-u3',
    name: 'Alex Turner',
    email: 'a.turner@corp.com',
    isOnline: true,
  },
  {
    id: 'catalog-u4',
    name: 'Maria Garcia',
    email: 'm.garcia@corp.com',
    isOnline: true,
  },
  {
    id: 'catalog-u5',
    name: 'Sam Chen',
    email: 's.chen@corp.com',
    isOnline: false,
  },
]

export const AVAILABLE_GROUPS_CATALOG: AssignableGroup[] = [
  {
    id: 'g1',
    name: 'Security Operations',
    memberCount: 42,
    description: 'Global threat monitoring and incident response team.',
  },
  {
    id: 'g2',
    name: 'Data Science',
    memberCount: 18,
    description: 'Advanced analytics, predictive modeling, and machine learning infrastructure.',
  },
  {
    id: 'g3',
    name: 'Marketing',
    memberCount: 12,
    description: 'External communications and brand strategy execution.',
  },
  {
    id: 'g4',
    name: 'Executive Board',
    memberCount: 5,
    description: 'High-level strategic oversight and top-tier access credentials.',
  },
  {
    id: 'g5',
    name: 'Alpha Team',
    memberCount: 8,
    description: 'Special projects and rapid deployment unit.',
  },
]

export const INITIAL_ROLE_ID = 'role-data-scientist-eu'

export const initialRoles: Role[] = [
  {
    id: INITIAL_ROLE_ID,
    name: 'Data_Scientist_EU',
    permissionCount: 8,
    userCount: 5,
    groupCount: 2,
    icon: 'shield',
  },
  {
    id: 'role-marketing-analyst',
    name: 'Marketing_Analyst',
    permissionCount: 3,
    userCount: 12,
    groupCount: 1,
    icon: 'shield',
  },
  {
    id: 'role-sysadmin-global',
    name: 'SysAdmin_Global',
    permissionCount: 142,
    userCount: 2,
    groupCount: 0,
    icon: 'shield_lock',
  },
]

const dataScientistPermissions: Permission[] = [
  {
    id: 'perm-db-1',
    resourceType: 'DATABASE',
    path: [{ label: 'prod_eu_central' }],
    effect: 'ALLOW',
    action: 'USAGE',
  },
  {
    id: 'perm-schema-1',
    resourceType: 'SCHEMA',
    path: [{ label: 'prod_eu_central' }, { label: 'analytics' }],
    effect: 'ALLOW',
    action: 'USAGE',
  },
  {
    id: 'perm-schema-2',
    resourceType: 'SCHEMA',
    path: [{ label: 'prod_eu_central' }, { label: 'raw_events' }],
    effect: 'ALLOW',
    action: 'USAGE',
  },
  {
    id: 'perm-table-1',
    resourceType: 'TABLE',
    path: [{ label: 'analytics' }, { label: 'user_metrics_agg' }],
    effect: 'ALLOW',
    action: 'SELECT',
  },
  {
    id: 'perm-table-2',
    resourceType: 'TABLE',
    path: [{ label: 'raw_events' }, { label: 'pii_dump_raw' }],
    effect: 'DENY',
    action: 'SELECT',
    isHighlighted: true,
  },
  {
    id: 'perm-table-3',
    resourceType: 'TABLE',
    path: [{ label: 'analytics' }, { label: 'regional_sales' }],
    effect: 'ALLOW',
    action: 'SELECT',
    modifier: { type: 'ROW_FILTER', label: 'Row Filter' },
  },
  {
    id: 'perm-table-4',
    resourceType: 'TABLE',
    path: [{ label: 'analytics' }, { label: 'staging_users' }],
    effect: 'ALLOW',
    action: 'SELECT',
  },
  {
    id: 'perm-column-1',
    resourceType: 'COLUMN',
    path: [{ label: 'users' }, { label: 'email' }],
    effect: 'ALLOW',
    action: 'SELECT',
    modifier: { type: 'COLUMN_MASK', label: 'Masked' },
  },
]

const marketingPermissions: Permission[] = [
  {
    id: 'perm-mkt-1',
    resourceType: 'DATABASE',
    path: [{ label: 'marketing_dw' }],
    effect: 'ALLOW',
    action: 'USAGE',
  },
  {
    id: 'perm-mkt-2',
    resourceType: 'TABLE',
    path: [{ label: 'campaigns' }, { label: 'daily_stats' }],
    effect: 'ALLOW',
    action: 'SELECT',
  },
  {
    id: 'perm-mkt-3',
    resourceType: 'TABLE',
    path: [{ label: 'campaigns' }, { label: 'spend_raw' }],
    effect: 'ALLOW',
    action: 'SELECT',
  },
]

const sysAdminPermissions: Permission[] = [
  {
    id: 'perm-admin-1',
    resourceType: 'DATABASE',
    path: [{ label: '*' }],
    effect: 'ALLOW',
    action: 'USAGE',
  },
]

export const initialPermissionsByRoleId: Record<string, Permission[]> = {
  [INITIAL_ROLE_ID]: dataScientistPermissions,
  'role-marketing-analyst': marketingPermissions,
  'role-sysadmin-global': sysAdminPermissions,
}

export const initialActorsByRoleId: Record<string, RoleActors> = {
  [INITIAL_ROLE_ID]: {
    users: [
      {
        id: 'user-1',
        name: 'Sarah Jenkins',
        email: 's.jenkins@corp.com',
        avatarUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuAI-tpkCHTk_FM-WIPVZAnP6qp6duhNSclr0aza5t7IkIxk2Q6kv5XtmNQeDFzW1dLSFyQeUhsAZ95jH2TsaO_SfoVC_3a14mLktyFJpz3yhRYLRvGQxdDOXBm3ZDjfOi8UJAjScT49VmoJfRCpQ7Uvlk__4z1EtSA59I07_09JuJx56flUDophxeDuJKmPI3anLjDlNzAKxjU0jf_mquFo8E-Q4-sjXz_K29BQ90oUjySOq3U-ovtO4mwxJF7F5mfIcZtnxSPj0BOI',
        isOnline: true,
      },
      {
        id: 'user-2',
        name: 'David Chen',
        email: 'd.chen@corp.com',
        avatarUrl:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuCpjjPnNHbyc37vNHJpTaEAnviVGOaKPUbC-e5VkXrmFGf4x57pd5snxs2MMOenatDs8fh1oOabanVp_JJv_EQornovXsbz9AmxsQf2OOC4BIKFazE_TdxR77lfppuhkmR7CGtENiK7Zut5DO7IlBT7zwzAqlCN-3fUD8hIHQy6c2ubt2yO13HJjSdtfTyR8RyEAMpFQNlfLqzGjO0xqA8Wp-6FyopCxF5l1It0wrQZR9QKcuZIJQfYH3fM5h94NUUjLZBoKLCabDOT',
        isOnline: true,
      },
      {
        id: 'user-3',
        name: 'Elena Rodriguez',
        email: 'e.rodriguez@corp.com',
        isOnline: false,
      },
      {
        id: 'user-4',
        name: 'James Wilson',
        email: 'j.wilson@corp.com',
        isOnline: true,
      },
      {
        id: 'user-5',
        name: 'Priya Sharma',
        email: 'p.sharma@corp.com',
        isOnline: false,
      },
    ],
    groups: [
      { id: 'group-1', name: 'EU_Data_Team', memberCount: 8 },
      { id: 'group-2', name: 'Global_Analytics_Read', memberCount: 4 },
    ],
    totalAffectedUsers: 17,
  },
  'role-marketing-analyst': {
    users: [
      { id: 'user-m1', name: 'Alice Smith', email: 'a.smith@insight.io', isOnline: true },
    ],
    groups: [{ id: 'group-m1', name: 'Marketing', memberCount: 12 }],
    totalAffectedUsers: 13,
  },
  'role-sysadmin-global': {
    users: [
      { id: 'user-s1', name: 'Bob Chen', email: 'b.chen@insight.io', isOnline: true },
      { id: 'user-s2', name: 'John Doe', email: 'john.doe@insight.io', isOnline: false },
    ],
    groups: [],
    totalAffectedUsers: 2,
  },
}
