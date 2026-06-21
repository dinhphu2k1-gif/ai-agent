import {
  type CheckboxProps,
  type FormControlLabelProps,
  Checkbox,
  FormControlLabel,
  Typography,
} from '@mui/material'
import { useFormContext, Controller } from 'react-hook-form'
// @mui

type RHFCheckboxProps = {
  name: string
  labelProps?: Omit<FormControlLabelProps, 'control' | 'label'>
  label?: string
} & Omit<CheckboxProps, 'variant'>

export default function RHFCheckbox({
  name,
  label,
  labelProps,
  ...other
}: RHFCheckboxProps): React.ReactNode {
  const { control } = useFormContext()

  return (
    <FormControlLabel
      label={label}
      {...labelProps}
      control={
        <Controller
          defaultValue={false}
          name={name}
          control={control}
          render={({ field, fieldState: { error } }) => (
            <>
              <Checkbox {...field} {...other} checked={field.value} />
              {!!error && (
                <Typography color={'error'} variant="caption" mt={1}>
                  {error?.message}
                </Typography>
              )}
            </>
          )}
        />
      }
    />
  )
}
