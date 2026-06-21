import { initialPermissionsByRoleId } from '@/pages/role-management/mock-data.dev'
import type { Permission } from '@/pages/role-management/types'
import type { AssignableMember, AssignableRoleOption, GroupMember, GroupRoleAssignment, UserGroup } from './types'

export { initialPermissionsByRoleId }

export const INITIAL_GROUP_ID = 'grp-de-core'

/** Direct grants on a group (not tied to an assigned role) */
export const initialPermissionsByGroupId: Record<string, Permission[]> = {
  [INITIAL_GROUP_ID]: [],
  'grp-marketing': [],
  'grp-contractors': [],
}

export const initialGroups: UserGroup[] = [
  {
    id: INITIAL_GROUP_ID,
    name: 'Data Engineering Core',
    memberCount: 12,
    roleCount: 3,
    createdAt: 'Oct 12, 2023',
    description: 'Core data platform engineering and pipeline operations.',
  },
  {
    id: 'grp-marketing',
    name: 'Marketing Analysts',
    memberCount: 8,
    roleCount: 2,
    createdAt: 'Jan 4, 2024',
    description: 'Campaign analytics and marketing data consumers.',
  },
  {
    id: 'grp-contractors',
    name: 'External Contractors',
    memberCount: 24,
    roleCount: 1,
    createdAt: 'Mar 22, 2024',
    description: 'Limited-access external collaborators.',
  },
]

export const membersByGroupId: Record<string, GroupMember[]> = {
  [INITIAL_GROUP_ID]: [
    {
      id: 'member-as',
      name: 'Alice Smith',
      email: 'alice.smith@datagate.co',
      initials: 'AS',
      status: 'Active',
    },
    {
      id: 'member-bj',
      name: 'Bob Jones',
      email: 'bob.jones@datagate.co',
      initials: 'BJ',
      status: 'Active',
    },
    {
      id: 'member-ec',
      name: 'Elena Rodriguez',
      email: 'e.rodriguez@datagate.co',
      initials: 'ER',
      status: 'Active',
    },
    {
      id: 'member-jw',
      name: 'James Wilson',
      email: 'j.wilson@datagate.co',
      initials: 'JW',
      status: 'Inactive',
    },
  ],
  'grp-marketing': [
    {
      id: 'member-m1',
      name: 'Maria Garcia',
      email: 'm.garcia@datagate.co',
      initials: 'MG',
      status: 'Active',
    },
    {
      id: 'member-m2',
      name: 'Sam Chen',
      email: 's.chen@datagate.co',
      initials: 'SC',
      status: 'Active',
    },
  ],
  'grp-contractors': [
    {
      id: 'member-c1',
      name: 'Alex Turner',
      email: 'a.turner@contractor.io',
      initials: 'AT',
      status: 'Active',
    },
  ],
}

const roleDataScientist: GroupRoleAssignment = {
  id: 'role-data-scientist-eu',
  name: 'Data Pipeline Admin',
  description:
    'Full access to manage and execute ETL pipelines across all production environments.',
  permissionCount: 8,
}

const roleMarketing: GroupRoleAssignment = {
  id: 'role-marketing-analyst',
  name: 'Warehouse Read-Only',
  description: 'Select access to core analytics schemas in the central data warehouse.',
  permissionCount: 3,
}

const roleAuditor: GroupRoleAssignment = {
  id: 'role-sysadmin-global',
  name: 'Platform Auditor',
  description: 'Read-only oversight across administrative resources.',
  permissionCount: 142,
}

export const rolesByGroupId: Record<string, GroupRoleAssignment[]> = {
  [INITIAL_GROUP_ID]: [roleDataScientist, roleMarketing, roleAuditor],
  'grp-marketing': [roleMarketing],
  'grp-contractors': [roleAuditor],
}

export const AVAILABLE_MEMBERS_CATALOG: AssignableMember[] = [
  {
    id: 'catalog-u1',
    name: 'Eleanor Vance',
    email: 'e.vance@corp.com',
    isOnline: true,
  },
  {
    id: 'catalog-u2',
    name: 'Julian Montague',
    email: 'j.montague@corp.com',
    isOnline: false,
  },
  {
    id: 'catalog-u3',
    name: 'Alex Turner',
    email: 'a.turner@corp.com',
    isOnline: true,
  },
  {
    id: 'catalog-u4',
    name: 'Priya Sharma',
    email: 'p.sharma@corp.com',
    isOnline: true,
  },
  {
    id: 'catalog-u5',
    name: 'David Chen',
    email: 'd.chen@corp.com',
    isOnline: false,
  },
]

export const AVAILABLE_ROLES_CATALOG: AssignableRoleOption[] = [
  {
    id: 'role-data-scientist-eu',
    name: 'Data Pipeline Admin',
    description: roleDataScientist.description,
    permissionCount: 8,
  },
  {
    id: 'role-marketing-analyst',
    name: 'Warehouse Read-Only',
    description: roleMarketing.description,
    permissionCount: 3,
  },
  {
    id: 'role-sysadmin-global',
    name: 'Platform Auditor',
    description: roleAuditor.description,
    permissionCount: 142,
  },
]
