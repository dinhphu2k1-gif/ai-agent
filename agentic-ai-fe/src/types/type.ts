import type { IconProps } from '@tabler/icons-react'
import type { ForwardRefExoticComponent, RefAttributes } from 'react'
import type {
  MenuType,
  UserStatus,
} from './enum'

export interface AuthenInfo {
  accessToken: string
  refreshToken?: string
}

export type IconMenu = ForwardRefExoticComponent<
  IconProps & RefAttributes<SVGSVGElement>
>

export interface Pages {
  id: string
  title: string
  caption?: string
  type?: MenuType
  breadcrumbs?: boolean
  icon?: IconMenu
  url?: string
  target?: boolean
  disabled?: boolean
  children?: Array<Pages>
}

export interface Pagesv1 {
  id: string
  path: string
  title: string
  caption?: string | null
  type?: MenuType
  icon?: string | null
  target?: boolean | null
  disabled?: boolean | null
  parentId?: string | null
  moduleId?: string | null
  children?: Array<Pagesv1>
}

export type PageForm = Omit<Pagesv1, 'children'>

export interface RegexTemplate {
  parttern: RegExp
  message: string
}

export interface RadioOption {
  value: string | number
  label: string
}

export interface PageableRequest {
  page: number
  pageSize: number
  sort?: string
  orderBy?: string
  [key: string]: number | string | undefined
}

export interface PageableResponse<T> {
  data: T[]
  currentPage: number
  totalItems: number
  totalPages: number
}

export interface User {
  id: string
  staffCode: string
  fullName: string
  email: string
  brcd: number
  depId: number
  status: UserStatus
  roles: string[]
}
