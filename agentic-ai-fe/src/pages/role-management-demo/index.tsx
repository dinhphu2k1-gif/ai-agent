import { useState } from 'react'
import { Box, Typography } from '@mui/material'

import RoleListPanel from './components/RoleListPanel'
import PermissionListPanel from './components/PermissionListPanel'
import ActorPanel from './components/ActorPanel'
import { AddPermissionDrawer } from '@/components/add-permission'

const RoleManagementPage = () => {
  const [selectedRole, setSelectedRole] = useState('analyst')
  const [isAddPermissionOpen, setIsAddPermissionOpen] = useState(false)

  const handleOpenDrawer = () => setIsAddPermissionOpen(true)
  const handleCloseDrawer = () => setIsAddPermissionOpen(false)

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        bgcolor: 'background.default',
        position: 'relative',
      }}
    >
      {/* Top App Bar */}
      <Box
        sx={{
          height: 64,
          minHeight: 64,
          bgcolor: 'surface',
          borderBottom: 1,
          borderColor: 'outlineVariant',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 3,
          zIndex: 10,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="displaySm" sx={{ color: 'onSurface' }}>
            Roles
          </Typography>
          <Box sx={{ px: 1, py: 0.5, bgcolor: 'surfaceContainerHigh', borderRadius: 1 }}>
            <Typography variant="labelMono" sx={{ color: 'onSurfaceVariant' }}>
              v2.4.0
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Main Content — 3-panel layout */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <RoleListPanel selectedRole={selectedRole} onSelect={setSelectedRole} />
        <PermissionListPanel role={selectedRole} onAddPermission={handleOpenDrawer} />
        <ActorPanel />
      </Box>

      {/* Add Permission Drawer */}
      <AddPermissionDrawer
        open={isAddPermissionOpen}
        onClose={handleCloseDrawer}
        contextLabel={selectedRole}
        contextIcon="shield"
        onSubmit={() => setIsAddPermissionOpen(false)}
      />

      {/* Backdrop overlay */}
      {isAddPermissionOpen && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            bgcolor: 'rgba(0,0,0,0.4)',
            zIndex: 30,
            backdropFilter: 'blur(2px)',
          }}
        />
      )}
    </Box>
  )
}

export default RoleManagementPage
