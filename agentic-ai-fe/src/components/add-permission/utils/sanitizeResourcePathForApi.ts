import type { ResourceNode } from '../types'

const SYNTHETIC_PATH_ID = /^(?:edit-.+-\d+|synthetic-path-\d+)$/

/** Never send FE-only synthetic ids to the policy API. */
export const sanitizeResourcePathForApi = (path: ResourceNode[]): ResourceNode[] =>
  path.map((node) => ({
    ...node,
    id: SYNTHETIC_PATH_ID.test(node.id) ? '' : node.id,
  }))
