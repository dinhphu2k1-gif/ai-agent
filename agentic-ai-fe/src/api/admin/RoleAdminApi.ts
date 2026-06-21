import type { AxiosRequestConfig } from 'axios'

import { mapRoleActors } from '@/api/mappers/adminActorMapper'
import {
  mapCatalogGroup,
  mapCatalogUser,
  mapRoleListItem,
} from '@/api/mappers/adminRoleMapper'
import {
  mapPermission,
  mapPermissionSummary,
} from '@/api/mappers/adminPermissionMapper'
import type { PermissionGrantPayload } from '@/components/add-permission'
import type {
  AssignableGroup,
  AssignableUser,
  Permission,
  PermissionSummary,
  Role,
  RoleActors,
} from '@/pages/role-management/types'
import type { PageableResponse } from '@/types/type'

import { normalizePermissionId } from './permissionId'
import { AdminApiService } from './AdminApiService'
import type {
  AdminCatalogGroupDto,
  AdminCatalogUserDto,
  AdminPermissionDto,
  AdminRoleDto,
} from './dto'
import { toAdminQueryParams, toListMeta } from './queryParams'
import { unwrapPage } from './unwrap'
import type {
  ActorsResponseDto,
  AdminListResult,
  AdminPageParams,
  CreateRoleBody,
  IdListBody,
  PermissionListResponse,
  RenameRoleBody,
} from './types'

class RoleAdminApi extends AdminApiService {
  async list(params: AdminPageParams, config?: AxiosRequestConfig): Promise<AdminListResult<Role>> {
    const page = await this.get<PageableResponse<AdminRoleDto>>('/roles', {
      ...config,
      params: toAdminQueryParams(params),
    })
    const { items, page: meta } = unwrapPage(page)

    return {
      items: items.map(mapRoleListItem),
      ...toListMeta(meta),
    }
  }

  async create(body: CreateRoleBody, config?: AxiosRequestConfig): Promise<Role> {
    const data = await this.post<AdminRoleDto, CreateRoleBody>('/roles', body, config)
    return mapRoleListItem(data)
  }

  async rename(roleId: string, body: RenameRoleBody, config?: AxiosRequestConfig): Promise<Role> {
    const data = await this.patch<AdminRoleDto, RenameRoleBody>(`/roles/${roleId}`, body, config)
    return mapRoleListItem(data)
  }

  async duplicate(roleId: string, config?: AxiosRequestConfig): Promise<Role> {
    const data = await this.post<AdminRoleDto>(`/roles/${roleId}/duplicate`, undefined, config)
    return mapRoleListItem(data)
  }

  async delete(roleId: string, config?: AxiosRequestConfig): Promise<void> {
    await this.deleteRequest<null>(`/roles/${roleId}`, config)
  }

  async getPermissions(
    roleId: string,
    config?: AxiosRequestConfig,
  ): Promise<{ permissions: Permission[]; summary: PermissionSummary | null }> {
    const data = await this.get<PermissionListResponse<AdminPermissionDto>>(
      `/roles/${roleId}/permissions`,
      config,
    )

    return {
      permissions: data.permissions.map(mapPermission),
      summary: mapPermissionSummary(data.summary),
    }
  }

  async grantPermission(
    roleId: string,
    body: PermissionGrantPayload,
    config?: AxiosRequestConfig,
  ): Promise<Permission[]> {
    const data = await this.post<{ created?: AdminPermissionDto[] }, PermissionGrantPayload>(
      `/roles/${roleId}/permissions`,
      body,
      config,
    )

    if (Array.isArray(data.created)) {
      return data.created.map(mapPermission)
    }

    if (Array.isArray(data)) {
      return (data as AdminPermissionDto[]).map(mapPermission)
    }

    return []
  }

  async updatePermission(
    roleId: string,
    permissionId: string,
    body: PermissionGrantPayload,
    config?: AxiosRequestConfig,
  ): Promise<Permission> {
    const data = await this.put<AdminPermissionDto, PermissionGrantPayload>(
      `/roles/${roleId}/permissions/${normalizePermissionId(permissionId)}`,
      body,
      config,
    )
    return mapPermission(data)
  }

  async deletePermission(
    roleId: string,
    permissionId: string,
    config?: AxiosRequestConfig,
  ): Promise<void> {
    await this.deleteRequest<null>(
      `/roles/${roleId}/permissions/${normalizePermissionId(permissionId)}`,
      config,
    )
  }

  async getActors(roleId: string, config?: AxiosRequestConfig): Promise<RoleActors> {
    const data = await this.get<ActorsResponseDto>(`/roles/${roleId}/actors`, config)
    return mapRoleActors(data)
  }

  async assignUsers(
    roleId: string,
    body: Pick<IdListBody, 'userIds'>,
    config?: AxiosRequestConfig,
  ): Promise<void> {
    await this.post<null, Pick<IdListBody, 'userIds'>>(`/roles/${roleId}/users`, body, config)
  }

  async unassignUser(roleId: string, userId: string, config?: AxiosRequestConfig): Promise<void> {
    await this.deleteRequest<null>(`/roles/${roleId}/users/${userId}`, config)
  }

  async assignGroups(
    roleId: string,
    body: Pick<IdListBody, 'groupIds'>,
    config?: AxiosRequestConfig,
  ): Promise<void> {
    await this.post<null, Pick<IdListBody, 'groupIds'>>(`/roles/${roleId}/groups`, body, config)
  }

  async unassignGroup(roleId: string, groupId: string, config?: AxiosRequestConfig): Promise<void> {
    await this.deleteRequest<null>(`/roles/${roleId}/groups/${groupId}`, config)
  }

  async listUsersCatalog(
    params: AdminPageParams,
    config?: AxiosRequestConfig,
  ): Promise<AdminListResult<AssignableUser>> {
    const page = await this.get<PageableResponse<AdminCatalogUserDto>>('/users/catalog', {
      ...config,
      params: toAdminQueryParams(params),
    })
    const { items, page: meta } = unwrapPage(page)

    return {
      items: items.map(mapCatalogUser),
      ...toListMeta(meta),
    }
  }

  async listGroupsCatalog(
    params: AdminPageParams,
    config?: AxiosRequestConfig,
  ): Promise<AdminListResult<AssignableGroup>> {
    const page = await this.get<PageableResponse<AdminCatalogGroupDto>>('/groups/catalog', {
      ...config,
      params: toAdminQueryParams(params),
    })
    const { items, page: meta } = unwrapPage(page)

    return {
      items: items.map(mapCatalogGroup),
      ...toListMeta(meta),
    }
  }
}

export default new RoleAdminApi()
