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

const channelSchema = z.object({
  title: z.string().trim().min(2, 'Channel name is too short').max(80, 'Channel name is too long'),
})

export type CreateChannelFormData = z.infer<typeof channelSchema>

interface CreateChannelDialogProps {
  open: boolean
  submitting?: boolean
  onClose: () => void
  onCreate: (data: CreateChannelFormData) => void | Promise<void>
}

const CreateChannelDialog = ({
  open,
  submitting = false,
  onClose,
  onCreate,
}: CreateChannelDialogProps) => {
  const methods = useForm<CreateChannelFormData>({
    resolver: zodResolver(channelSchema),
    defaultValues: { title: '' },
  })

  const { handleSubmit, reset } = methods

  useEffect(() => {
    if (!open) reset({ title: '' })
  }, [open, reset])

  const handleCancel = () => {
    reset()
    onClose()
  }

  const handleFormSubmit = async (data: CreateChannelFormData) => {
    try {
      await onCreate(data)
      reset()
      onClose()
    } catch {
      // Parent shows toast
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
          gap: 1.5,
          borderBottom: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerHigh)',
        }}
      >
        <Typography variant="headlineAgent" sx={{ flex: 1 }}>
          New chat channel
        </Typography>
        <IconButton onClick={handleCancel} size="small" sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
            close
          </span>
        </IconButton>
      </DialogTitle>

      <FormProvider
        methods={methods}
        onSubmit={handleSubmit(handleFormSubmit)}
        sx={{ display: 'flex', flexDirection: 'column' }}
      >
        <DialogContent sx={{ p: 2, bgcolor: 'var(--mui-palette-surfaceContainer)' }}>
          <Box sx={{ pt: 1 }}>
            <Typography
              variant="labelMono"
              sx={{ color: 'var(--mui-palette-onSurfaceVariant)', mb: 0.5, display: 'block' }}
            >
              Channel name
            </Typography>
            <RHFTextField name="title" placeholder="e.g. Q4 revenue analysis" autoFocus />
          </Box>
        </DialogContent>

        <DialogActions
          sx={{
            p: 2,
            borderTop: 1,
            borderColor: 'var(--mui-palette-outlineVariant)',
            bgcolor: 'var(--mui-palette-surfaceContainerLow)',
            gap: 1,
          }}
        >
          <Button onClick={handleCancel} sx={{ color: 'var(--mui-palette-onSurfaceVariant)', textTransform: 'none' }}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={submitting}>
            Create channel
          </Button>
        </DialogActions>
      </FormProvider>
    </Dialog>
  )
}

export default CreateChannelDialog
