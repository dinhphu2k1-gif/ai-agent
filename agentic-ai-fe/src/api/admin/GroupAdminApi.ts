import type { AxiosRequestConfig } from 'axios'

import {
  mapCatalogMember,
  mapCatalogRoleOption,
  mapGroupListItem,
  mapGroupMember,
  mapGroupRoleAssignment,
} from '@/api/mappers/adminGroupMapper'
import {
  mapEffectivePermission,
  mapInheritedSummary,
  mapPermission,
  mapPermissionSummary,
} from '@/api/mappers/adminPermissionMapper'
import type { PermissionGrantPayload } from '@/components/add-permission'
import type {
  AssignableMember,
  AssignableRoleOption,
  EffectivePermission,
  GroupMember,
  GroupRoleAssignment,
  InheritedSummary,
  UserGroup,
} from '@/pages/group-management/types'
import type { Permission, PermissionSummary } from '@/pages/role-management/types'
import type { PageableResponse } from '@/types/type'

import { normalizePermissionId } from './permissionId'
import { AdminApiService } from './AdminApiService'
import type {
  AdminCatalogRoleDto,
  AdminCatalogUserDto,
  AdminEffectivePermissionDto,
  AdminGroupDto,
  AdminGroupMemberDto,
  AdminGroupRoleDto,
  AdminPermissionDto,
} from './dto'
import { toAdminQueryParams, toListMeta } from './queryParams'
import { unwrapPage } from './unwrap'
import type {
  AdminListResult,
  AdminPageParams,
  CreateGroupBody,
  EffectivePermissionListResponse,
  IdListBody,
  PermissionListResponse,
} from './types'

class GroupAdminApi extends AdminApiService {
  async list(params: AdminPageParams, config?: AxiosRequestConfig): Promise<AdminListResult<UserGroup>> {
    const page = await this.get<PageableResponse<AdminGroupDto>>('/groups', {
      ...config,
      params: toAdminQueryParams(params),
    })
    const { items, page: meta } = unwrapPage(page)

    return {
      items: items.map(mapGroupListItem),
      ...toListMeta(meta),
    }
  }

  async create(body: CreateGroupBody, config?: AxiosRequestConfig): Promise<UserGroup> {
    const data = await this.post<AdminGroupDto, CreateGroupBody>('/groups', body, config)
    return mapGroupListItem(data)
  }

  async delete(groupId: string, config?: AxiosRequestConfig): Promise<void> {
    await this.deleteRequest<null>(`/groups/${groupId}`, config)
  }

  async getMembers(groupId: string, config?: AxiosRequestConfig): Promise<GroupMember[]> {
    const data = await this.get<AdminGroupMemberDto[]>(`/groups/${groupId}/members`, config)
    return data.map(mapGroupMember)
  }

  async addMembers(
    groupId: string,
    body: Pick<IdListBody, 'memberIds'>,
    config?: AxiosRequestConfig,
  ): Promise<void> {
    await this.post<null, Pick<IdListBody, 'memberIds'>>(
      `/groups/${groupId}/members`,
      body,
      config,
    )
  }

  async removeMember(
    groupId: string,
    memberId: string,
    config?: AxiosRequestConfig,
  ): Promise<void> {
    await this.deleteRequest<null>(`/groups/${groupId}/members/${memberId}`, config)
  }

  async listMembersCatalog(
    params: AdminPageParams,
    config?: AxiosRequestConfig,
  ): Promise<AdminListResult<AssignableMember>> {
    const page = await this.get<PageableResponse<AdminCatalogUserDto>>('/members/catalog', {
      ...config,
      params: toAdminQueryParams(params),
    })
    const { items, page: meta } = unwrapPage(page)

    return {
      items: items.map(mapCatalogMember),
      ...toListMeta(meta),
    }
  }

  async getRoles(groupId: string, config?: AxiosRequestConfig): Promise<GroupRoleAssignment[]> {
    const data = await this.get<AdminGroupRoleDto[]>(`/groups/${groupId}/roles`, config)
    return data.map(mapGroupRoleAssignment)
  }

  async assignRoles(
    groupId: string,
    body: Pick<IdListBody, 'roleIds'>,
    config?: AxiosRequestConfig,
  ): Promise<void> {
    await this.post<null, Pick<IdListBody, 'roleIds'>>(`/groups/${groupId}/roles`, body, config)
  }

  async unassignRole(groupId: string, roleId: string, config?: AxiosRequestConfig): Promise<void> {
    await this.deleteRequest<null>(`/groups/${groupId}/roles/${roleId}`, config)
  }

  async listRolesCatalog(
    params: AdminPageParams,
    config?: AxiosRequestConfig,
  ): Promise<AdminListResult<AssignableRoleOption>> {
    const page = await this.get<PageableResponse<AdminCatalogRoleDto>>('/roles/catalog', {
      ...config,
      params: toAdminQueryParams(params),
    })
    const { items, page: meta } = unwrapPage(page)

    return {
      items: items.map(mapCatalogRoleOption),
      ...toListMeta(meta),
    }
  }

  async getEffectivePermissions(
    groupId: string,
    config?: AxiosRequestConfig,
  ): Promise<{
    permissions: EffectivePermission[]
    summary: PermissionSummary | null
    inheritedSummary: InheritedSummary | null
  }> {
    const data = await this.get<EffectivePermissionListResponse<AdminEffectivePermissionDto>>(
      `/groups/${groupId}/effective-permissions`,
      config,
    )

    return {
      permissions: data.permissions.map(mapEffectivePermission),
      summary: mapPermissionSummary(data.summary),
      inheritedSummary: mapInheritedSummary(data.inheritedSummary),
    }
  }

  async grantPermission(
    groupId: string,
    body: PermissionGrantPayload,
    config?: AxiosRequestConfig,
  ): Promise<Permission[]> {
    const data = await this.post<{ created?: AdminPermissionDto[] }, PermissionGrantPayload>(
      `/groups/${groupId}/permissions`,
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
    groupId: string,
    permissionId: string,
    body: PermissionGrantPayload,
    config?: AxiosRequestConfig,
  ): Promise<Permission> {
    const data = await this.put<AdminPermissionDto, PermissionGrantPayload>(
      `/groups/${groupId}/permissions/${normalizePermissionId(permissionId)}`,
      body,
      config,
    )
    return mapPermission(data)
  }

  async deletePermission(
    groupId: string,
    permissionId: string,
    config?: AxiosRequestConfig,
  ): Promise<void> {
    await this.deleteRequest<null>(
      `/groups/${groupId}/permissions/${normalizePermissionId(permissionId)}`,
      config,
    )
  }
}

export default new GroupAdminApi()
