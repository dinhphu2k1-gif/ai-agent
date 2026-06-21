/**
 * FE edit flow once used synthetic resource node ids `edit-{permissionId}-{index}`.
 * If those leak into URL path params, normalize back to the real permission id.
 */
export const normalizePermissionId = (id: string): string => {
  const syntheticPathNode = /^edit-(.+)-\d+$/.exec(id)
  if (syntheticPathNode) {
    return syntheticPathNode[1]
  }
  return id
}
