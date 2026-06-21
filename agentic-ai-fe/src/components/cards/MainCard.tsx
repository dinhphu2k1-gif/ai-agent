import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  type SxProps,
  Typography,
} from '@mui/material'
import { useTheme, type Theme } from '@mui/material/styles'
import { forwardRef } from 'react'

// material-ui

// constant
const headerSX = {
  '& .MuiCardHeader-action': { mr: 0 },
}

// ==============================|| CUSTOM MAIN CARD ||============================== //

interface MainCardProps {
  border?: boolean
  children?: React.ReactNode
  content?: boolean
  contentClass?: string
  contentSX?: SxProps<Theme>
  darkTitle?: boolean
  secondary?: React.ReactNode
  shadow?: string
  sx?: SxProps<Theme>
  title?: React.ReactNode
}

const MainCard = forwardRef<HTMLDivElement, MainCardProps>(
  (
    {
      border = true,
      children,
      content = true,
      contentClass = '',
      contentSX = {},
      darkTitle,
      secondary,
      sx = {},
      title,
      ...others
    },
    ref
  ) => {
    const theme = useTheme()

    return (
      <Card
        ref={ref}
        variant="elevation"
        {...others}
        sx={{
          border: border ? '1px solid' : 'none',
          borderColor: theme.palette.primary[200] || '',
          boxShadow: '0 2px 14px 0 rgb(32 40 45 / 8%)',
          ':hover': {
            boxShadow: '0 2px 14px 0 rgb(32 40 45 / 20%)',
          },
          ...sx,
        }}
      >
        {/* card header and action */}
        {title && (
          <CardHeader
            sx={headerSX}
            title={
              darkTitle ? <Typography variant="h3">{title}</Typography> : title
            }
            action={secondary}
          />
        )}

        {/* content & header divider */}
        {title && <Divider />}

        {/* card content */}
        {content && (
          <CardContent sx={contentSX} className={contentClass}>
            {children}
          </CardContent>
        )}
        {!content && children}
      </Card>
    )
  }
)

MainCard.displayName = 'MainCard'

export default MainCard
