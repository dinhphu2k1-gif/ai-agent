// material-ui
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord'
import {
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  useMediaQuery,
} from '@mui/material'
import { useTheme } from '@mui/material/styles'

import { IconChevronRight, IconChevronDown } from '@tabler/icons-react'

import { forwardRef, type ReactNode, useMemo } from 'react'
import { useAppDispatch } from '@/redux/hooks'
import type { IconMenu, Pages } from '@/types/type'
import { Link, useLocation } from 'react-router-dom'
import { setOpen } from '@/redux/reducers/sidebar'

interface NavItemProps {
  item: Pages
  level: number
  url: string
  navClose?: boolean
  isItemCollapse?: boolean
  isOpenCollapse?: boolean
  isSubItem?: boolean
}

const NavItem = ({
  item,
  level,
  url,
  isItemCollapse = false,
  isOpenCollapse = false,
}: NavItemProps): ReactNode => {
  const theme = useTheme()
  const dispatch = useAppDispatch()
  const { pathname } = useLocation()
  const matchesMd = useMediaQuery(theme.breakpoints.down('md'))

  const isSelected = useMemo(() => pathname === (item.url || url), [pathname, item.url, url])

  const Icon = item.icon as IconMenu
  const itemIcon = item?.icon ? (
    <Icon stroke={1.5} size="1.2rem" />
  ) : (
    <FiberManualRecordIcon
      sx={{
        width: isSelected ? 6 : 4,
        height: isSelected ? 6 : 4,
      }}
      fontSize={level > 0 ? 'inherit' : 'medium'}
    />
  )

  const itemHandler = (): void => {
    if (matchesMd) dispatch(setOpen(false))
  }

  const listItemProps = {
    component: isItemCollapse
      ? undefined
      : forwardRef<HTMLAnchorElement>((props, ref) => (
          <Link
            ref={ref}
            {...props}
            to={item.url || url || ''}
            target={item.target ? '_blank' : '_self'}
          />
        )),
  }

  return (
    <ListItemButton
      {...listItemProps}
      disabled={item.disabled}
      sx={{
        borderRadius: 1,
        mb: 0.25,
        alignItems: 'center',
        backgroundColor: 'transparent',
        py: 0.75,
        px: 1.5,
        color: theme.vars.palette.onSurfaceVariant,
        '&.Mui-selected': {
          bgcolor: 'color-mix(in srgb, var(--mui-palette-primary-main) 10%, transparent)',
          color: theme.vars.palette.primary.main,
          '&:hover': {
            bgcolor: theme.vars.palette.surfaceContainerHigh,
          },
          '& .MuiListItemIcon-root': {
            color: theme.vars.palette.primary.main,
          },
        },
        '&:hover': {
          bgcolor: theme.vars.palette.surfaceContainerHigh,
          color: theme.vars.palette.onSurface,
          '& .MuiListItemIcon-root': {
            color: theme.vars.palette.onSurface,
          },
        },
      }}
      selected={isSelected}
      onClick={() => itemHandler()}
    >
      <ListItemIcon
        sx={{
          minWidth: 28,
          color: 'inherit',
        }}
      >
        {itemIcon}
      </ListItemIcon>
      <ListItemText
        primary={
          <Typography variant="bodyMain" color="inherit">
            {item.title}
          </Typography>
        }
      />
      {isItemCollapse &&
        (isOpenCollapse ? (
          <IconChevronRight style={{ width: 14, height: 14 }} />
        ) : (
          <IconChevronDown style={{ width: 14, height: 14 }} />
        ))}
    </ListItemButton>
  )
}

export default NavItem
