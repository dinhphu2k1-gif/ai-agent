export enum MenuType {
  Group = 1,
  Collapse,
  Item,
}

export enum UserStatus {
  Acitive = 1,
  InActive,
  Deleted,
}

export enum ApproveStatus {
  Pending,
  Approved,
  Reject,
}

export enum ScreenTab {
  List,
  Approve,
  ApproveOther,
}

export enum AuthorType {
  Global,
  HeadOffice,
  BranchI,
  Branch,
  HeadOfficeBranchI,
  DeparmentHeadOffice,
}

export enum AllowPerType {
  Global,
  HeadOffice,
}

export enum ApproveType {
  Approve = 1,
  Deny,
}

export enum DiffType {
  Default = 'default',
  New = 'success',
  Delete = 'error',
}
