import type { DataTable, DataTableColumn } from './types'

const SQL_FENCE_RE = /```sql\s*([\s\S]*?)```/i

const splitPipeRow = (line: string): string[] =>
  line
    .split('|')
    .map((cell) => cell.trim())
    .filter((cell, index, arr) => {
      if (cell.length > 0) return true
      return arr.length > 1 && index > 0 && index < arr.length - 1
    })

const isSeparatorRow = (line: string): boolean => /^[\s|+\-:=]+$/.test(line.trim())

const columnKey = (label: string, index: number): string => {
  const slug = label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')

  return slug || `col_${index}`
}

export interface ParsedSqlResultBlock {
  sql: string
  title?: string
  dataTable: DataTable
  remainderText: string
}

const parsePreviewTable = (
  text: string,
): { title?: string; dataTable: DataTable; remainderText: string } | null => {
  const previewLineIndex = text.search(/^Preview:\s*$/im)
  if (previewLineIndex === -1) return null

  // Take everything after the "Preview:" marker and parse the first table-looking block.
  const afterPreview = text.slice(previewLineIndex).replace(/^Preview:\s*/im, '').trim()
  const lines = afterPreview.split('\n').map((line) => line.trimEnd())
  if (lines.length < 2) return null

  const headerCells = splitPipeRow(lines[0])
  if (headerCells.length === 0) return null

  // Require a separator row right after header to avoid false positives.
  if (!isSeparatorRow(lines[1] ?? '')) return null

  const columns: DataTableColumn[] = headerCells.map((label, index) => ({
    key: columnKey(label, index),
    label,
  }))

  const rows: Record<string, string>[] = []
  for (let i = 2; i < lines.length; i += 1) {
    const line = lines[i]
    if (!line.trim()) break
    if (isSeparatorRow(line)) continue
    const cells = splitPipeRow(line)
    if (cells.length === 0) break

    const row: Record<string, string> = {}
    columns.forEach((col, index) => {
      row[col.key] = cells[index] ?? ''
    })
    rows.push(row)
  }

  if (rows.length === 0) return null

  // Remove the preview table block from the original text to get remainder.
  const tableBlock = ['Preview:', ...lines.slice(0, Math.min(lines.length, rows.length + 2))].join(
    '\n',
  )
  const remainderText = text.replace(tableBlock, '').replace(/\n{3,}/g, '\n\n').trim()

  const title = 'SQL preview'
  return { title, dataTable: { title, columns, rows }, remainderText }
}

export const parseSqlResultBlock = (text: string): ParsedSqlResultBlock | null => {
  const fenceMatch = text.match(SQL_FENCE_RE)
  if (!fenceMatch) {
    const previewOnly = parsePreviewTable(text)
    if (!previewOnly) return null
    return {
      sql: '',
      title: previewOnly.title,
      dataTable: previewOnly.dataTable,
      remainderText: previewOnly.remainderText,
    }
  }

  const inner = fenceMatch[1].trim()
  const previewIndex = inner.search(/^Preview:\s*$/im)
  if (previewIndex === -1) return null

  const beforePreview = inner.slice(0, previewIndex).trim()
  const afterPreview = inner.slice(previewIndex).replace(/^Preview:\s*/im, '').trim()
  const tableLines = afterPreview.split('\n').map((line) => line.trimEnd())

  if (tableLines.length < 2) return null

  const headerCells = splitPipeRow(tableLines[0])
  if (headerCells.length === 0) return null

  const columns: DataTableColumn[] = headerCells.map((label, index) => ({
    key: columnKey(label, index),
    label,
  }))

  const dataLines = tableLines.slice(1).filter((line) => line.trim() && !isSeparatorRow(line))
  const rows: Record<string, string>[] = []

  for (const line of dataLines) {
    const cells = splitPipeRow(line)
    if (cells.length === 0) continue

    const row: Record<string, string> = {}
    columns.forEach((col, index) => {
      row[col.key] = cells[index] ?? ''
    })
    rows.push(row)
  }

  if (rows.length === 0) return null

  const beforePreviewLines = beforePreview
    .split('\n')
    .map((line) => line.trimEnd())
    .filter((line) => line.trim().length > 0)

  // The agent output is usually:
  // SQL:
  // <query...>
  // Rows: <n> (optional)
  //
  // Avoid regexes with multiline `$` (they can truncate SQL to the first line).
  let sqlLines = [...beforePreviewLines]
  if (sqlLines[0] && /^SQL:\s*$/i.test(sqlLines[0].trim())) {
    sqlLines = sqlLines.slice(1)
  } else if (sqlLines[0] && /^SQL:\s*/i.test(sqlLines[0])) {
    sqlLines[0] = sqlLines[0].replace(/^SQL:\s*/i, '')
  }

  sqlLines = sqlLines.filter((line) => !/^Rows:\s*\d+\s*$/i.test(line.trim()))

  const sqlBody = sqlLines.join('\n').trim()
  const rowsMeta = beforePreview.match(/^Rows:\s*(\d+)\s*$/im)
  const title = rowsMeta ? `Query results (${rowsMeta[1]} rows)` : 'Query results'

  const remainder = text
    .replace(fenceMatch[0], '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  return {
    sql: sqlBody,
    title,
    dataTable: { title, columns, rows },
    remainderText: remainder,
  }
}
