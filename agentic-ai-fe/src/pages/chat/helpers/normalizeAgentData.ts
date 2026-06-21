import type { AgentMessageData, DataTable, DataTableColumn, TableRow } from '@/api/chat'

import { parseSqlResultBlock } from '@/api/chat/parseSqlResultBlock'

const SQL_FENCE_ONLY = /^```sql[\s\S]*```$/i

const LEGACY_COLUMNS: DataTableColumn[] = [
  { key: 'region', label: 'Region' },
  { key: 'actual', label: 'Actual (M)' },
  { key: 'projected', label: 'Projected (M)' },
  { key: 'variance', label: 'Variance' },
]

const legacyTableToDataTable = (tableHeader: string | undefined, tableRows: TableRow[]): DataTable => ({
  title: tableHeader ?? 'Results',
  columns: LEGACY_COLUMNS,
  rows: tableRows.map((row) => ({
    region: row.region,
    actual: row.actual,
    projected: row.projected,
    variance: row.variance,
  })),
})

const inferDataTableFromRows = (
  tableHeader: string | undefined,
  rawRows: Record<string, unknown>[],
): DataTable | null => {
  if (rawRows.length === 0) return null

  const first = rawRows[0]
  const keys = Object.keys(first)
  if (keys.length === 0) return null

  const columns: DataTableColumn[] = keys.map((key) => ({
    key,
    label: key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase()),
  }))

  const rows = rawRows.map((row) => {
    const normalized: Record<string, string> = {}
    keys.forEach((key) => {
      normalized[key] = row[key] != null ? String(row[key]) : ''
    })
    return normalized
  })

  return {
    title: tableHeader ?? 'Query results',
    columns,
    rows,
  }
}

const applySqlParagraphParsing = (data: AgentMessageData): AgentMessageData | null => {
  const paragraphs = [...data.paragraphs]
  let parsedBlock: ReturnType<typeof parseSqlResultBlock> | null = null
  let parsedIndex = -1

  for (let i = 0; i < paragraphs.length; i += 1) {
    const result = parseSqlResultBlock(paragraphs[i])
    if (result) {
      parsedBlock = result
      parsedIndex = i
      break
    }
  }

  if (!parsedBlock || parsedIndex === -1) return null

  paragraphs[parsedIndex] = parsedBlock.remainderText

  return {
    ...data,
    paragraphs: paragraphs.filter((p) => p.trim().length > 0),
    sqlQuery: parsedBlock.sql,
    dataTable: parsedBlock.dataTable,
  }
}

export const normalizeAgentData = (data: AgentMessageData): AgentMessageData => {
  if (data.dataTable) {
    return {
      ...data,
      paragraphs: data.paragraphs.filter((p) => !p.match(SQL_FENCE_ONLY)),
    }
  }

  const fromSql = applySqlParagraphParsing(data)
  if (fromSql) return fromSql

  if (data.tableRows && data.tableRows.length > 0) {
    const first = data.tableRows[0] as TableRow & Record<string, unknown>
    if ('region' in first && 'actual' in first) {
      return {
        ...data,
        dataTable: legacyTableToDataTable(data.tableHeader, data.tableRows),
      }
    }

    const dynamic = inferDataTableFromRows(
      data.tableHeader,
      data.tableRows as unknown as Record<string, unknown>[],
    )
    if (dynamic) {
      return { ...data, dataTable: dynamic }
    }
  }

  return data
}
