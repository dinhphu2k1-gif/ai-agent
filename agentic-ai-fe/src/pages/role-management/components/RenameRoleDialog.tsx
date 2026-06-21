import { useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  IconButton,
  Button,
} from '@mui/material'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { FormProvider, RHFTextField } from '@/components/hook-form'

const renameSchema = z.object({
  name: z
    .string()
    .min(2, 'Role name is too short')
    .regex(/^[a-zA-Z0-9_]+$/, 'Use letters, numbers, and underscores only'),
})

type RenameRoleFormData = z.infer<typeof renameSchema>

interface RenameRoleDialogProps {
  open: boolean
  initialName: string
  submitting?: boolean
  onClose: () => void
  onSubmit: (name: string) => void | Promise<void>
}

const RenameRoleDialog = ({
  open,
  initialName,
  submitting = false,
  onClose,
  onSubmit,
}: RenameRoleDialogProps) => {
  const methods = useForm<RenameRoleFormData>({
    resolver: zodResolver(renameSchema),
    defaultValues: { name: initialName },
  })

  const { handleSubmit, reset } = methods

  useEffect(() => {
    if (open) reset({ name: initialName })
  }, [open, initialName, reset])

  const handleCancel = () => {
    reset({ name: initialName })
    onClose()
  }

  const handleFormSubmit = async (data: RenameRoleFormData) => {
    try {
      await onSubmit(data.name)
      onClose()
    } catch {
      // Parent shows toast; keep dialog open
    }
  }

  return (
    <Dialog
      open={open}
      onClose={handleCancel}
      maxWidth="xs"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            bgcolor: 'var(--mui-palette-surfaceContainer)',
            backgroundImage: 'none',
            borderRadius: 2,
            border: 1,
            borderColor: 'var(--mui-palette-outlineVariant)',
          },
        },
      }}
    >
      <DialogTitle
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerHigh)',
        }}
      >
        <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
          Rename role
        </Typography>
        <IconButton onClick={handleCancel} size="small" aria-label="Close">
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            close
          </span>
        </IconButton>
      </DialogTitle>

      <FormProvider methods={methods} onSubmit={handleSubmit(handleFormSubmit)}>
        <DialogContent sx={{ p: 2, pt: 2 }}>
          <Box>
            <Typography
              variant="labelMono"
              sx={{ color: 'var(--mui-palette-onSurfaceVariant)', mb: 0.5, display: 'block' }}
            >
              Role name
            </Typography>
            <RHFTextField name="name" placeholder="e.g. Data_Scientist_EU" />
          </Box>
        </DialogContent>

        <DialogActions
          sx={{
            p: 2,
            borderTop: 1,
            borderColor: 'var(--mui-palette-outlineVariant)',
            bgcolor: 'var(--mui-palette-surfaceContainerLow)',
          }}
        >
          <Button onClick={handleCancel} sx={{ color: 'onSurfaceVariant', textTransform: 'none' }}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={submitting} sx={{ textTransform: 'none' }}>
            Save
          </Button>
        </DialogActions>
      </FormProvider>
    </Dialog>
  )
}

export default RenameRoleDialog
