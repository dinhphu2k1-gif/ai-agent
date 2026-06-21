import type { RadioOption } from '@/types/type'
import {
  FormControlLabel,
  type FormControlLabelProps,
  Radio,
  RadioGroup,
  type RadioGroupProps,
  Typography,
} from '@mui/material'
import React from 'react'
import { Controller, useFormContext } from 'react-hook-form'

type RHFRadioGroupProps = {
  options: Array<RadioOption>
  name: string
  formControlLabelProps?: FormControlLabelProps
} & Omit<RadioGroupProps, 'variant'>

export default function RHFRadioGroup({
  name,
  options,
  formControlLabelProps,
  ...other
}: RHFRadioGroupProps): React.ReactNode {
  const { control } = useFormContext()
  return (
    <Controller
      name={name}
      control={control}
      defaultValue={null}
      render={({ field, fieldState: { error } }) => (
        <>
          <RadioGroup
            {...field}
            {...other}
            onChange={(e) =>
              field.onChange(
                typeof options[0].value === 'number'
                  ? Number(e.target.value)
                  : e
              )
            }
          >
            {options.map((option) => (
              <FormControlLabel
                {...formControlLabelProps}
                value={option.value}
                control={<Radio />}
                label={option.label}
                key={option.value}
              />
            ))}
          </RadioGroup>
          {!!error && (
            <Typography color={'error'} variant="caption" mt={1}>
              {error?.message}
            </Typography>
          )}
        </>
      )}
    />
  )
}
