import {
  Autocomplete,
  type AutocompleteProps,
  TextField,
  type TextFieldProps,
} from '@mui/material'
import { useFormContext, Controller } from 'react-hook-form'

export type RHFAutocompleteProps<Value> = {
  name: string
  label?: string
  options: ReadonlyArray<Value>
  textFieldProps?: TextFieldProps
} & Omit<AutocompleteProps<Value, boolean, false, false>, 'renderInput'>

export default function RHFAutocomplete<Value>({
  name,
  label,
  options,
  textFieldProps,
  ...other
}: RHFAutocompleteProps<Value>): React.ReactNode {
  const { control } = useFormContext()
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <Autocomplete
          {...field}
          options={options}
          renderInput={(params) => (
            <TextField
              label={label}
              {...params}
              {...textFieldProps}
              error={!!error}
              helperText={error?.message}
            />
          )}
          onChange={(_, data) => field.onChange(data)}
          {...other}
        />
      )}
    />
  )
}
