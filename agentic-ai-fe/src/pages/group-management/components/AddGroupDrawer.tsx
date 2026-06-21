import { Drawer, Box, Typography, IconButton, Button } from '@mui/material'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { FormProvider, RHFTextField } from '@/components/hook-form'

const groupSchema = z.object({
  name: z.string().min(2, 'Group name is too short'),
  description: z.string().optional(),
})

export type GroupFormData = z.infer<typeof groupSchema>

interface AddGroupDrawerProps {
  open: boolean
  onClose: () => void
  onAdd: (data: GroupFormData) => void | Promise<void>
  submitting?: boolean
}

const AddGroupDrawer = ({ open, onClose, onAdd, submitting = false }: AddGroupDrawerProps) => {
  const methods = useForm<GroupFormData>({
    resolver: zodResolver(groupSchema),
    defaultValues: { name: '', description: '' },
  })

  const { handleSubmit, reset } = methods

  const handleCancel = () => {
    reset()
    onClose()
  }

  const handleFormSubmit = (data: GroupFormData) => {
    onAdd(data)
    reset()
    onClose()
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
          New Group
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
            Group Name
          </Typography>
          <RHFTextField name="name" placeholder="e.g., Data Engineering Core" />
        </Box>
        <Box>
          <Typography
            variant="labelMono"
            sx={{ color: 'var(--mui-palette-onSurfaceVariant)', mb: 0.5, display: 'block' }}
          >
            Description (optional)
          </Typography>
          <RHFTextField name="description" placeholder="Short description of this group" />
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
            Create Group
          </Button>
        </Box>
      </FormProvider>
    </Drawer>
  )
}

export default AddGroupDrawer
