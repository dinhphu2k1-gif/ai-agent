import { AllowPerType, AuthorType, MenuType } from './enum'
import type { RadioOption } from './type'

// theme constant
export const gridSpacing = 3
export const drawerWidth = 260
export const appDrawerWidth = 320
export const heightHeader = 54

// cookies key
export const cookiesKey = '_authen-info'
export const SESSTION_USER_KEY = '_user'

export const loginUrl =
  import.meta.env.VITE_LOGIN_URL || 'https://iam-fe.dev.agribank.com.vn'

export const MESSAGE_COMMON = {
  ERROR_COMMON: 'Có lỗi xảy ra. Vui lòng thử lại!',
  CLIENT_ERROR: 'Đã xảy ra lỗi mạng hoặc lỗi không mong muốn',
}

export const MESSAGE_FORM = {
  REQUIRE: 'Trường này bắt buộc nhập',
  TYPE_ERROR: 'Bắt buộc hoặc giá trị không hợp lệ',
}

export const BRCD_HEAD_OFFICE = 1050

export const MENU_TYPE_OPTIONS: Array<RadioOption> = [
  {
    label: 'Màn hình con',
    value: MenuType.Item,
  },
  {
    label: 'Cụm màn hình',
    value: MenuType.Collapse,
  },
]

export const AUTHOR_OPTIONS = {
  [AuthorType.Global]: 'Toàn hệ thống',
  [AuthorType.HeadOffice]: 'Trụ sở chính',
  [AuthorType.HeadOfficeBranchI]: 'Trụ sở chính & CN loại I',
  [AuthorType.BranchI]: 'CN loại I',
  [AuthorType.Branch]: 'Chi nhánh',
  [AuthorType.DeparmentHeadOffice]: 'Phòng ban trụ sở chính',
}

export const ALLOW_OPTIONS = {
  [AllowPerType.Global]: 'NQT tại chi nhánh',
  [AllowPerType.HeadOffice]: 'NQT toàn hệ thống',
}
