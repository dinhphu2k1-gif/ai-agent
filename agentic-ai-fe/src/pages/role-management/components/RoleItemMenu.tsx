import { Box, IconButton } from '@mui/material'

interface RoleItemMenuProps {
  onRename: () => void
  onDelete: () => void
  deleteDisabled?: boolean
}

const RoleItemMenu = ({ onRename, onDelete, deleteDisabled = false }: RoleItemMenuProps) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
      <IconButton
        size="small"
        aria-label="Rename role"
        onClick={(e) => {
          e.stopPropagation()
          onRename()
        }}
        sx={{ color: 'onSurfaceVariant' }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
          edit
        </span>
      </IconButton>
      <IconButton
        size="small"
        disabled={deleteDisabled}
        aria-label="Delete role"
        onClick={(e) => {
          e.stopPropagation()
          onDelete()
        }}
        sx={{ color: 'onSurfaceVariant', '&:hover': { color: 'error.main' } }}
      >
        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
          delete
        </span>
      </IconButton>
    </Box>
  )
}

export default RoleItemMenu
