import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Button,
  MenuItem,
  Chip,
  Stack,
  Divider,
} from '@mui/material'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { FormProvider, RHFSelect, RHFTextField } from '@/components/hook-form'

const userSchema = z.object({
  fullName: z.string().min(2, 'Name is too short'),
  email: z.email('Invalid email address'),
  username: z.string().min(3, 'Username must be at least 3 characters'),
  groups: z.array(z.string()),
  roles: z.array(z.string()),
  isActive: z.boolean(),
})

export type UserFormData = z.infer<typeof userSchema>

interface AddUserDrawerProps {
  open: boolean
  onClose: () => void
  onAdd: (data: UserFormData) => void | Promise<void>
  groupOptions: string[]
  roleOptions: string[]
  optionsLoading?: boolean
  submitting?: boolean
}

const AddUserDrawer = ({
  open,
  onClose,
  onAdd,
  groupOptions,
  roleOptions,
  optionsLoading = false,
  submitting = false,
}: AddUserDrawerProps) => {
  const methods = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      fullName: '',
      email: '',
      username: '',
      groups: [],
      roles: [],
      isActive: true,
    },
  })

  const { handleSubmit, reset } = methods

  const handleFormSubmit = async (data: UserFormData) => {
    try {
      await onAdd(data)
      reset()
    } catch {
      // Parent shows toast; keep drawer open for correction
    }
  }

  const handleCancel = () => {
    reset()
    onClose()
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      // onClose={handleCancel}
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
      {/* Header */}
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
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Typography variant="headlineAgent" sx={{ color: 'var(--mui-palette-onSurface)' }}>
            Thêm Tài Khoản
          </Typography>
          <Typography variant="bodyData" sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}>
            Thêm tài khoản mới vào hệ thống
          </Typography>
        </Box>
        <IconButton onClick={handleCancel} size="small">
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      {/* Body */}
      <FormProvider
        methods={methods}
        id="add-user-form"
        onSubmit={handleSubmit(handleFormSubmit)}
        sx={{ flex: 1, overflowY: 'auto', p: 2 }}
      >
        {/* Thông tin tài khoản */}
        <Stack spacing={3}>
          <Stack spacing={1}>
            <Typography variant="h5">Thông tin tài khoản</Typography>
            <Divider flexItem />
            <Stack spacing={2} sx={{ pt: 1 }}>
              <Box>
                <Typography
                  variant="labelMono"
                  sx={{
                    color: 'var(--mui-palette-onSurfaceVariant)',
                    mb: 0.5,
                    display: 'block',
                  }}
                >
                  Họ và tên
                </Typography>
                <RHFTextField name="fullName" fullWidth placeholder="e.g., Jane Doe" />
              </Box>
              <Box>
                <Typography
                  variant="labelMono"
                  sx={{
                    color: 'var(--mui-palette-onSurfaceVariant)',
                    mb: 0.5,
                    display: 'block',
                  }}
                >
                  Username
                </Typography>
                <RHFTextField name="username" fullWidth placeholder="janedoe" size="small" />
              </Box>
              <Box>
                <Typography
                  variant="labelMono"
                  sx={{
                    color: 'var(--mui-palette-onSurfaceVariant)',
                    mb: 0.5,
                    display: 'block',
                  }}
                >
                  Email
                </Typography>
                <RHFTextField name="email" fullWidth placeholder="jane.doe@crimson.io" />
              </Box>
            </Stack>
          </Stack>

          {/* Access Control */}
          <Stack spacing={1}>
            <Typography variant="h5">Kiểm soát truy cập</Typography>
            <Divider flexItem />
            <Stack spacing={2} sx={{ pt: 1 }}>
              <Box>
                <Typography
                  variant="labelMono"
                  sx={{
                    color: 'var(--mui-palette-onSurfaceVariant)',
                    mb: 0.5,
                    display: 'block',
                  }}
                >
                  Nhóm người dùng
                </Typography>
                <RHFSelect
                  formControlProps={{ fullWidth: true }}
                  name="groups"
                  multiple
                  displayEmpty
                  renderValue={(selected) => {
                    if ((selected as string[]).length === 0) {
                      return (
                        <Typography
                          variant="bodyMain"
                          sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}
                        >
                          Select groups...
                        </Typography>
                      )
                    }
                    return (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(selected as string[]).map((value) => (
                          <Chip
                            key={value}
                            label={value}
                            size="small"
                            sx={{
                              bgcolor: 'var(--mui-palette-secondaryContainer)',
                              color: 'var(--mui-palette-onSecondaryContainer)',
                              borderRadius: 1,
                              fontSize: '10px',
                              height: 20,
                            }}
                          />
                        ))}
                      </Box>
                    )
                  }}
                >
                  {groupOptions.map((group) => (
                    <MenuItem key={group} value={group} disabled={optionsLoading}>
                      {group}
                    </MenuItem>
                  ))}
                </RHFSelect>
              </Box>

              <Box>
                <Typography
                  variant="labelMono"
                  sx={{
                    color: 'var(--mui-palette-onSurfaceVariant)',
                    mb: 0.5,
                    display: 'block',
                  }}
                >
                  Role
                </Typography>
                <RHFSelect
                  formControlProps={{ fullWidth: true }}
                  name="roles"
                  multiple
                  displayEmpty
                  renderValue={(selected) => {
                    if ((selected as string[]).length === 0) {
                      return (
                        <Typography
                          variant="bodyMain"
                          sx={{ color: 'var(--mui-palette-onSurfaceVariant)' }}
                        >
                          Select roles...
                        </Typography>
                      )
                    }
                    return (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(selected as string[]).map((value) => (
                          <Chip
                            key={value}
                            label={value}
                            size="small"
                            sx={{
                              bgcolor: 'var(--mui-palette-primaryContainer)',
                              color: 'var(--mui-palette-onPrimaryContainer)',
                              borderRadius: 1,
                              fontSize: '10px',
                              height: 20,
                            }}
                          />
                        ))}
                      </Box>
                    )
                  }}
                >
                  {roleOptions.map((role) => (
                    <MenuItem key={role} value={role} disabled={optionsLoading}>
                      {role}
                    </MenuItem>
                  ))}
                </RHFSelect>
              </Box>
            </Stack>
          </Stack>
        </Stack>
      </FormProvider>

      {/* Footer */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerLow)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 2,
        }}
      >
        <Button
          onClick={handleCancel}
          sx={{
            color: 'var(--mui-palette-onSurfaceVariant)',
            textTransform: 'none',
            fontWeight: 600,
          }}
        >
          Cancel
        </Button>
        <Button
          form="add-user-form"
          type="submit"
          variant="contained"
          disabled={submitting || optionsLoading}
          startIcon={<span className="material-symbols-outlined">person_add</span>}
        >
          Add User
        </Button>
      </Box>
    </Drawer>
  )
}

export default AddUserDrawer
