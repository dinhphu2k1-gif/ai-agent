import { Box, type BoxProps } from '@mui/material'

type TabPanelProps = {
  children?: React.ReactNode
  index: number
  value: number
} & BoxProps

export default function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
    >
      {value === index && (
        <Box sx={{ p: 2 }} {...other}>
          {children}
        </Box>
      )}
    </div>
  )
}
