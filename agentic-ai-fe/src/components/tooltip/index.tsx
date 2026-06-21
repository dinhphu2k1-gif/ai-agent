import {
  styled,
  Tooltip,
  tooltipClasses,
  type TooltipProps,
} from '@mui/material'
import { forwardRef } from 'react'

const HtmlTooltip = styled(
  forwardRef<HTMLDivElement, TooltipProps>(({ className, ...props }, ref) => (
    <Tooltip ref={ref} {...props} arrow classes={{ popper: className }} />
  ))
)(({ theme }) => ({
  [`& .${tooltipClasses.tooltip}`]: {
    backgroundColor: theme.palette.background.paper,
    maxWidth: 500,
    maxHeight: 'calc(100vh - 64px)',
    minWidth: 205,
    boxShadow: theme.shadows[10],
    paddingLeft: 0,
    paddingRight: 0,
    '::-webkit-scrollbar': {
      width: '6px',
      height: '6px',
    },
    '& ::-webkit-scrollbar-track': {
      backgroundColor: theme.palette.background.paper,
    },
    '& ::-webkit-scrollbar-thumb': {
      borderRadius: '8px',
      backgroundColor: 'grey',
    },
  },
  [`& .${tooltipClasses.arrow}`]: {
    color: theme.palette.background.paper,
  },
}))

export default HtmlTooltip
