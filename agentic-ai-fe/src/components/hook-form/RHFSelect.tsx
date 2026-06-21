import {
  FormControl,
  type FormControlProps,
  InputLabel,
  type SelectProps,
  Select,
  FormHelperText,
} from '@mui/material'
import type { ReactNode } from 'react'
import { Controller, useFormContext } from 'react-hook-form'

export type RHFSelectProps = {
  name: string
  label?: string
  formControlProps?: FormControlProps
  children: ReactNode
} & SelectProps

export default function RHFSelect({
  name,
  label,
  children,
  formControlProps,
  ...other
}: RHFSelectProps): ReactNode {
  const { control } = useFormContext()
  return (
    <FormControl
      {...formControlProps}
      sx={{
        '.MuiInputAdornment-root': {
          visibility: 'hidden',
        },
        ':hover': {
          '.MuiInputAdornment-root': {
            visibility: 'visible',
          },
        },
        ...formControlProps?.sx,
      }}
    >
      {label && <InputLabel id={label}>{label}</InputLabel>}
      <Controller
        name={name}
        defaultValue={''}
        control={control}
        render={({ field, fieldState: { error } }) => (
          <>
            <Select {...field} labelId={label} label={label} {...other}>
              {children}
            </Select>
            {!!error && (
              <FormHelperText sx={{ color: 'error.main' }}>{error?.message}</FormHelperText>
            )}
          </>
        )}
      />
    </FormControl>
  )
}
