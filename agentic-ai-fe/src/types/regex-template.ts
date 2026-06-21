import type { RegexTemplate } from './type'

export const PATH: RegexTemplate = {
  parttern: /^[a-z]+(-[a-z]+)*$/,
  message: 'Chỉ chữ thường và ký tự (-). Ký tự (-) không ở cuối',
}

export const FEATURE_CODE: RegexTemplate = {
  parttern: /^[A-Z]+(_[A-Z]+)*$/,
  message: 'Chỉ chữ in hoa và ký tự (_). Ký tự (_) không ở cuối',
}
export const EMAIL: RegexTemplate = {
  parttern: /^[A-Za-z0-9._%+-]+@agribank\.com\.vn$/,
  message: 'Chỉ mail của Agribank',
}
