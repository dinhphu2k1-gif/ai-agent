// form
import { Box, type BoxProps } from '@mui/material'
import type { ReactNode } from 'react'
import { type FieldValues, FormProvider as Form, type UseFormReturn } from 'react-hook-form'

type CustomProviderProps<T extends FieldValues> = {
  methods: UseFormReturn<T>
  onSubmit?: React.ChangeEventHandler<HTMLFormElement>
  children: React.ReactNode
} & BoxProps

export default function FormProvider<T extends FieldValues>({
  children,
  onSubmit,
  methods,
  ...other
}: CustomProviderProps<T>): ReactNode {
  return (
    <Form {...methods}>
      <Box component={'form'} onSubmit={onSubmit} {...other}>
        {children}
      </Box>
    </Form>
  )
}
