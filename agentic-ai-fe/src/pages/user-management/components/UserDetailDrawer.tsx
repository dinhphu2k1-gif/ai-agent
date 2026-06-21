import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Avatar,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
} from '@mui/material'
import type { User } from './UserTable'

interface UserDetailDrawerProps {
  user: User | null
  open: boolean
  loading?: boolean
  roleMutationSubmitting?: boolean
  onClose: () => void
  onAddRole: () => void
  onRemoveRole: (roleName: string) => void
}

const UserDetailDrawer = ({
  user,
  open,
  loading = false,
  roleMutationSubmitting = false,
  onClose,
  onAddRole,
  onRemoveRole,
}: UserDetailDrawerProps) => {
  const rolesDisabled = loading || roleMutationSubmitting
  if (!user) return null

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      slotProps={{
        paper: {
          sx: {
            width: 400,
            background: 'var(--mui-palette-surfaceContainerLow)',
            // background: 'var(--mui-palette-surfaceContainerLowest)',
            borderLeft: 1,
            borderColor: 'outlineVariant',
          },
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar
            variant="rounded"
            sx={{
              width: 64,
              height: 64,
              bgcolor: 'secondaryContainer',
              color: 'onSecondaryContainer',
              fontWeight: 'bold',
              fontSize: '24px',
              borderRadius: 3,
            }}
          >
            {user.initials}
          </Avatar>
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography variant="displaySm" sx={{ fontWeight: 'bold', color: 'onSurface' }}>
              {user.name}
            </Typography>
            <Typography variant="bodyMain" sx={{ color: 'onSurfaceVariant' }}>
              {user.email}
            </Typography>
            <Box sx={{ mt: 0.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: user.status === 'Active' ? '#34d399' : 'onSurfaceVariant',
                }}
              />
              <Typography variant="labelMono" sx={{ color: 'onSurfaceVariant' }}>
                {user.status}
              </Typography>
            </Box>
          </Box>
        </Box>
        <IconButton size="small" onClick={onClose} sx={{ color: 'onSurfaceVariant' }}>
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      {/* Content */}
      <Box
        sx={{ flex: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}
      >
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={32} />
          </Box>
        )}

        {/* Groups */}
        <Box
          sx={{
            // bgcolor: 'surfaceContainerLow',
            bgcolor: 'surfaceContainerLowest',
            borderRadius: 1,
            p: 1.5,
            border: 1,
            borderColor: 'outlineVariant',
          }}
        >
          <Box
            sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}
          >
            <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
              Groups
            </Typography>
            <Button
              size="small"
              startIcon={
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  add
                </span>
              }
              sx={{ color: 'primary.main', textTransform: 'none' }}
            >
              Add
            </Button>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {user.groups.map((group) => (
              <Box
                key={group}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                  pl: 1,
                  pr: 0.5,
                  py: 0.5,
                  borderRadius: 1,
                  bgcolor: 'var(--mui-palette-groupBg)',
                  border: 1,
                  borderColor: 'tertiaryContainer',
                }}
              >
                <Typography variant="labelMono" sx={{ color: 'tertiary' }}>
                  {group}
                </Typography>
                <IconButton
                  size="small"
                  sx={{ p: 0.25, color: 'onSurfaceVariant', '&:hover': { color: 'error.main' } }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 12 }}>
                    close
                  </span>
                </IconButton>
              </Box>
            ))}
          </Box>
        </Box>

        {/* Roles */}
        <Box
          sx={{
            // bgcolor: 'surfaceContainerLow',
            bgcolor: 'surfaceContainerLowest',
            borderRadius: 1,
            p: 1.5,
            border: 1,
            borderColor: 'outlineVariant',
          }}
        >
          <Box
            sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}
          >
            <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
              Roles
            </Typography>
            <Button
              size="small"
              disabled={rolesDisabled}
              onClick={onAddRole}
              startIcon={
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  add
                </span>
              }
              sx={{ color: 'primary.main', textTransform: 'none' }}
            >
              Add
            </Button>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {user.roles.map((role) => (
              <Box
                key={role}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                  pl: 1,
                  pr: 0.5,
                  py: 0.5,
                  borderRadius: 1,
                  bgcolor: 'var(--mui-palette-roleAdminBg)',
                  border: 1,
                  borderColor: 'primaryContainer',
                }}
              >
                <Typography variant="labelMono" sx={{ color: 'primaryFixed' }}>
                  {role}
                </Typography>
                <IconButton
                  size="small"
                  disabled={rolesDisabled}
                  onClick={() => onRemoveRole(role)}
                  aria-label={`Remove role ${role}`}
                  sx={{ p: 0.25, color: 'onSurfaceVariant', '&:hover': { color: 'error.main' } }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 12 }}>
                    close
                  </span>
                </IconButton>
              </Box>
            ))}
          </Box>
        </Box>

        {/* Effective Permissions */}
        <Accordion
          sx={{
            bgcolor: 'surfaceContainerLow',
            border: 1,
            borderColor: 'outlineVariant',
            borderRadius: 1,
            '&:before': { display: 'none' },
            boxShadow: 'none',
            '&.Mui-expanded': {
              m: 0,
            },
          }}
        >
          <AccordionSummary
            expandIcon={
              <span
                className="material-symbols-outlined"
                style={{ color: 'var(--mui-palette-on-surface-variant)' }}
              >
                expand_more
              </span>
            }
            sx={{
              bgcolor: 'surfaceContainerHigh',
              '&:hover': { bgcolor: 'surfaceBright' },
              borderRadius: 1,
              px: 1.5,
              '&.Mui-expanded': {
                borderBottom: 1,
                borderColor: 'outlineVariant',
                borderBottomLeftRadius: 0,
                borderBottomRightRadius: 0,
              },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <span
                className="material-symbols-outlined"
                style={{ color: 'var(--mui-palette-on-surface-variant)' }}
              >
                shield
              </span>
              <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
                Effective Permissions
              </Typography>
            </Box>
            <Box
              sx={{
                ml: 'auto',
                mr: 1,
                px: 1,
                py: 0.25,
                borderRadius: 1,
                bgcolor: 'surfaceVariant',
                color: 'onSurfaceVariant',
                fontSize: '10px',
                fontWeight: 'bold',
              }}
            >
              42 Total
            </Box>
          </AccordionSummary>
          <AccordionDetails
            sx={{ p: 1.5, bgcolor: 'surfaceContainerLowest', borderRadius: '0 0 4px 4px' }}
          >
            <Typography variant="bodyData" sx={{ color: 'onSurfaceVariant', mb: 1 }}>
              Permissions are inherited from assigned groups and roles.
            </Typography>
            <Button
              size="small"
              sx={{
                color: 'primary.main',
                textTransform: 'none',
                p: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
              }}
            >
              View detailed matrix{' '}
              <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
                open_in_new
              </span>
            </Button>
          </AccordionDetails>
        </Accordion>
      </Box>

      {/* Footer */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          bgcolor: 'surfaceContainerLow',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 1,
        }}
      >
        <Button
          variant="outlined"
          onClick={onClose}
          sx={{ color: 'onSurface', borderColor: 'outlineVariant', textTransform: 'none', px: 2 }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          color="primary"
          sx={{ fontWeight: 'bold', textTransform: 'none', px: 2 }}
        >
          Save Changes
        </Button>
      </Box>
    </Drawer>
  )
}

export default UserDetailDrawer
