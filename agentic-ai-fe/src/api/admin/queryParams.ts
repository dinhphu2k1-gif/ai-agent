import type { AdminPageParams } from './types'

export const toAdminQueryParams = (
  params: AdminPageParams,
): Record<string, string | number> => {
  const query: Record<string, string | number> = {
    page: params.page,
    pageSize: params.pageSize,
  }

  if (params.search) query.search = params.search
  if (params.sort) query.sort = params.sort
  if (params.orderBy) query.orderBy = params.orderBy
  if (params.status) query.status = params.status

  return query
}

export const toListMeta = (page: {
  currentPage: number
  totalItems: number
  totalPages: number
}) => ({
  currentPage: page.currentPage,
  totalItems: page.totalItems,
  totalPages: page.totalPages,
})
