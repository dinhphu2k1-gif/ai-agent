import type { AxiosRequestConfig } from 'axios'

import { mapResourceTree } from '@/api/mappers/adminResourceMapper'
import type { ResourceNode } from '@/components/add-permission/types'

import { AdminApiService } from './AdminApiService'
import type { AdminResourceNodeDto } from './dto'

class ResourceAdminApi extends AdminApiService {
  async getTree(config?: AxiosRequestConfig): Promise<ResourceNode[]> {
    const data = await this.get<AdminResourceNodeDto[] | { tree?: AdminResourceNodeDto[] }>(
      '/resources/tree',
      config,
    )

    if (Array.isArray(data)) {
      return mapResourceTree(data)
    }

    if (data.tree && Array.isArray(data.tree)) {
      return mapResourceTree(data.tree)
    }

    return []
  }
}

export default new ResourceAdminApi()
