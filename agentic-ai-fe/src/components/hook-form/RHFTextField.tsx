// form
import { TextField, type TextFieldProps } from '@mui/material'
import type { ReactNode } from 'react'
import { useFormContext, Controller } from 'react-hook-form'
// @mui

export type RHFTextFieldProps = {
  name: string
} & Omit<TextFieldProps, 'variant'>

export default function RHFTextField({
  name,
  ...other
}: RHFTextFieldProps): ReactNode {
  const { control } = useFormContext()

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          {...other}
          error={!!error}
          helperText={error?.message || other.helperText}
        />
      )}
    />
  )
}
