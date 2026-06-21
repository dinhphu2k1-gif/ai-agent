import {
  type FormControlLabelProps,
  type SwitchProps,
  FormControlLabel,
  Switch,
  Typography,
} from '@mui/material'
import { useFormContext, Controller } from 'react-hook-form'
// @mui

type RHFSwitchProps = {
  name: string
  labelProps?: Omit<FormControlLabelProps, 'control' | 'label'>
  label?: string
} & Omit<SwitchProps, 'variant'>

export default function RHFSwitch({
  name,
  label,
  labelProps,
  ...other
}: RHFSwitchProps): React.ReactNode {
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
              <Switch {...field} {...other} checked={field.value} />
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
