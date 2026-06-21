import { Grid } from '@mui/material'
import type { ReactNode } from 'react'

interface GroupManagementWorkspaceProps {
  groupList: ReactNode
  groupDetail: ReactNode
  permissions: ReactNode
}

const GroupManagementWorkspace = ({
  groupList,
  groupDetail,
  permissions,
}: GroupManagementWorkspaceProps) => {
  return (
    <Grid
      container
      spacing={0}
      sx={{
        flex: 1,
        minHeight: 0,
        width: '100%',
        alignItems: 'stretch',
        alignContent: 'flex-start',
        overflow: { xs: 'auto', lg: 'hidden' },
      }}
    >
      {groupList}
      {groupDetail}
      {permissions}
    </Grid>
  )
}

export default GroupManagementWorkspace
