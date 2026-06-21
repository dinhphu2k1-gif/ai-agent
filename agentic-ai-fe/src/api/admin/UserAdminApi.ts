import type { AxiosRequestConfig } from 'axios'

import { mapUserDetail, mapUserListItem } from '@/api/mappers/adminUserMapper'
import type { User } from '@/pages/user-management/components/UserTable'
import type { PageableResponse } from '@/types/type'

import { AdminApiService } from './AdminApiService'
import type { AdminUserDetailDto, AdminUserDto } from './dto'
import { toAdminQueryParams, toListMeta } from './queryParams'
import { unwrapPage } from './unwrap'
import type {
  AdminListResult,
  AdminPageParams,
  BulkAssignGroupsBody,
  BulkAssignRolesBody,
  BulkDeactivateBody,
  BulkMutationResult,
  CreateUserBody,
  NameOptionsResponse,
} from './types'

class UserAdminApi extends AdminApiService {
  async list(params: AdminPageParams, config?: AxiosRequestConfig): Promise<AdminListResult<User>> {
    const page = await this.get<PageableResponse<AdminUserDto>>('/users', {
      ...config,
      params: toAdminQueryParams(params),
    })
    const { items, page: meta } = unwrapPage(page)

    return {
      items: items.map(mapUserListItem),
      ...toListMeta(meta),
    }
  }

  async getById(userId: string, config?: AxiosRequestConfig): Promise<User> {
    const data = await this.get<AdminUserDetailDto>(`/users/${userId}`, config)
    return mapUserDetail(data)
  }

  async create(body: CreateUserBody, config?: AxiosRequestConfig): Promise<User> {
    const data = await this.post<AdminUserDto, CreateUserBody>('/users', body, config)
    return mapUserListItem(data)
  }

  async getGroupOptions(config?: AxiosRequestConfig): Promise<NameOptionsResponse> {
    return this.get<NameOptionsResponse>('/groups/options', config)
  }

  async getRoleOptions(config?: AxiosRequestConfig): Promise<NameOptionsResponse> {
    return this.get<NameOptionsResponse>('/roles/options', config)
  }

  async bulkAssignGroups(
    body: BulkAssignGroupsBody,
    config?: AxiosRequestConfig,
  ): Promise<BulkMutationResult> {
    return this.post<BulkMutationResult, BulkAssignGroupsBody>(
      '/users/bulk/assign-groups',
      body,
      config,
    )
  }

  async bulkAssignRoles(
    body: BulkAssignRolesBody,
    config?: AxiosRequestConfig,
  ): Promise<BulkMutationResult> {
    return this.post<BulkMutationResult, BulkAssignRolesBody>(
      '/users/bulk/assign-roles',
      body,
      config,
    )
  }

  async bulkDeactivate(
    body: BulkDeactivateBody,
    config?: AxiosRequestConfig,
  ): Promise<BulkMutationResult> {
    return this.post<BulkMutationResult, BulkDeactivateBody>(
      '/users/bulk/deactivate',
      body,
      config,
    )
  }
}

export default new UserAdminApi()
