import { Drawer, Box, Typography, IconButton, Button } from '@mui/material'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { FormProvider, RHFTextField } from '@/components/hook-form'

const roleSchema = z.object({
  name: z
    .string()
    .min(2, 'Role name is too short')
    .regex(/^[a-zA-Z0-9_]+$/, 'Use letters, numbers, and underscores only'),
})

export type RoleFormData = z.infer<typeof roleSchema>

interface AddRoleDrawerProps {
  open: boolean
  onClose: () => void
  onAdd: (data: RoleFormData) => void | Promise<void>
  submitting?: boolean
}

const AddRoleDrawer = ({ open, onClose, onAdd, submitting = false }: AddRoleDrawerProps) => {
  const methods = useForm<RoleFormData>({
    resolver: zodResolver(roleSchema),
    defaultValues: { name: '' },
  })

  const { handleSubmit, reset } = methods

  const handleCancel = () => {
    reset()
    onClose()
  }

  const handleFormSubmit = async (data: RoleFormData) => {
    try {
      await onAdd(data)
      reset()
      onClose()
    } catch {
      // Parent shows toast; keep drawer open
    }
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      slotProps={{
        paper: {
          sx: {
            width: 440,
            bgcolor: 'var(--mui-palette-surface)',
            display: 'flex',
            flexDirection: 'column',
            backgroundImage: 'none',
          },
        },
      }}
    >
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerLow)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography variant="headlineAgent" sx={{ color: 'var(--mui-palette-onSurface)' }}>
          New Role
        </Typography>
        <IconButton onClick={handleCancel} size="small" aria-label="Close">
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      <FormProvider
        methods={methods}
        onSubmit={handleSubmit(handleFormSubmit)}
        sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 2, gap: 2 }}
      >
        <Box>
          <Typography
            variant="labelMono"
            sx={{ color: 'var(--mui-palette-onSurfaceVariant)', mb: 0.5, display: 'block' }}
          >
            Role Name
          </Typography>
          <RHFTextField name="name" placeholder="e.g., Data_Analyst_EU" />
        </Box>

        <Box sx={{ mt: 'auto', display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          <Button onClick={handleCancel} sx={{ color: 'onSurfaceVariant', textTransform: 'none' }}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={submitting}
            sx={{ textTransform: 'none' }}
          >
            Create Role
          </Button>
        </Box>
      </FormProvider>
    </Drawer>
  )
}

export default AddRoleDrawer
