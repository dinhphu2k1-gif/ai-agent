import {
  DatePicker,
  type DatePickerProps,
} from '@mui/x-date-pickers/DatePicker'
import type { ReactNode } from 'react'
import { useFormContext, Controller } from 'react-hook-form'

export type RHFDateFieldProps = {
  name: string
} & DatePickerProps<boolean>

export default function RHFDatePicker({
  name,
  ...other
}: RHFDateFieldProps): ReactNode {
  const { control } = useFormContext()
  return (
    <Controller
      name={name}
      control={control}
      render={({ field: { onChange, value }, fieldState: { error } }) => {
        return (
          <DatePicker
            value={value}
            onChange={(event) => {
              onChange(event)
            }}
            {...other}
            slotProps={{
              ...other.slotProps,
              textField: {
                ...other.slotProps?.textField,
                error: !!error,
                helperText: error?.message,
              },
            }}
          />
        )
      }}
    />
  )
}
