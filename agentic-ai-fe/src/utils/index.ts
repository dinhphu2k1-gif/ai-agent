import type { AxiosResponse } from 'axios'
import { isAxiosError } from 'axios'
import type { ApiResponse } from '@/api'
import { MESSAGE_COMMON } from '@/types/constant'



/**
 * Download file
 * @param data Blob data
 * @param fileName name of file
 * @returns
 */
export function downloadFile(data: BlobPart, fileName: string): void {
  try {
    const downloadUrl = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.log(error)
    throw error
  }
}

/**
 * Get default name of file in reponse
 * @param response axios reponse
 * @returns name of file in headers
 */
export function getNameFile(response: AxiosResponse): string | undefined {
  const contentDisposition = response.headers['content-disposition']
  let filename
  if (contentDisposition && contentDisposition.indexOf('attachment') !== -1) {
    const matches = /filename[^;=\n]*=((['"]).*?\2|([^;\n]*))/gi.exec(
      contentDisposition
    )
    if (matches != null && matches[1]) {
      filename = matches[1].replace(/['"]/g, '')
    }
  }
  return filename
}

/**
 * Handle exception for axios
 * @param error exception
 */
export function handleException(error: unknown): string {
  if (isAxiosError(error) && error.response) {
    const response: ApiResponse<null> = error.response.data
    return response.message
  } else {
    return MESSAGE_COMMON.CLIENT_ERROR
  }
}

export function enumToValues<T extends object>(enumObj: T): Array<T[keyof T]> {
  const values = Object.values(enumObj)
  const filtered = values.filter(
    (v) => typeof v !== 'string' || !Object.keys(enumObj).includes(v as string)
  )
  return filtered as Array<T[keyof T]>
}
