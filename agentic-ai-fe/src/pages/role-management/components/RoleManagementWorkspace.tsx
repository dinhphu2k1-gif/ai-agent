import { Grid } from '@mui/material'
import type { ReactNode } from 'react'

interface RoleManagementWorkspaceProps {
  roleList: ReactNode
  permissions: ReactNode
  actors: ReactNode
}

const RoleManagementWorkspace = ({ roleList, permissions, actors }: RoleManagementWorkspaceProps) => {
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
      {roleList}
      {permissions}
      {actors}
    </Grid>
  )
}

export default RoleManagementWorkspace
