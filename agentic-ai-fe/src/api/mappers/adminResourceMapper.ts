import type { AdminResourceNodeDto } from '@/api/admin/dto'
import { ResourceType, type ResourceNode } from '@/components/add-permission/types'

const mapResourceType = (value: string): ResourceType => {
  const normalized = value.toLowerCase()
  if (normalized === 'database') return ResourceType.Database
  if (normalized === 'schema') return ResourceType.Schema
  if (normalized === 'column') return ResourceType.Column
  return ResourceType.Table
}

export const mapResourceNode = (dto: AdminResourceNodeDto): ResourceNode => ({
  id: dto.id,
  name: dto.name,
  type: mapResourceType(dto.type),
  isPrimaryKey: dto.isPrimaryKey,
  isForeignKey: dto.isForeignKey,
  children: dto.children?.map(mapResourceNode),
})

export const mapResourceTree = (nodes: AdminResourceNodeDto[]): ResourceNode[] =>
  nodes.map(mapResourceNode)
