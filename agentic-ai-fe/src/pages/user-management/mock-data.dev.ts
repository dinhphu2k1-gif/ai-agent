import type { User } from './components/UserTable'

export const mockUsers: User[] = [
  {
    id: 'user-1',
    name: 'Sarah Jenkins',
    email: 's.jenkins@corp.com',
    status: 'Active',
    groups: ['EU_Data_Team'],
    roles: ['Data_Scientist_EU'],
    lastActive: '2 hours ago',
    initials: 'SJ',
  },
  {
    id: 'user-2',
    name: 'David Chen',
    email: 'd.chen@corp.com',
    status: 'Active',
    groups: ['Global_Analytics_Read'],
    roles: ['Data_Scientist_EU'],
    lastActive: '1 day ago',
    initials: 'DC',
  },
  {
    id: 'user-3',
    name: 'Elena Rodriguez',
    email: 'e.rodriguez@corp.com',
    status: 'Inactive',
    groups: ['Marketing'],
    roles: ['Marketing_Analyst'],
    lastActive: '3 weeks ago',
    initials: 'ER',
  },
]
