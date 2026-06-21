// material-ui
import { MenuType } from '@/types/enum'
import type { Pages } from '@/types/type'
import { List, Typography, ListSubheader } from '@mui/material'
import { useTheme } from '@mui/material/styles'

// project imports
import NavCollapse from '../NavCollapse/NavCollapse'
import NavItem from '../NavItem'

// ==============================|| SIDEBAR MENU LIST GROUP ||============================== //

interface NavGroupProps {
  item: Pages
}

const NavGroup = ({ item }: NavGroupProps): React.ReactNode => {
  const theme = useTheme()

  // menu list collapse & items
  const items = item.children?.map((menu) => {
    switch (menu.type) {
      case MenuType.Collapse:
        return <NavCollapse key={menu.id} menu={menu} level={1} url={`${menu.id}`} />
      case MenuType.Item:
        return <NavItem key={menu.id} item={menu} level={1} url={`${menu.id}`} />
      default:
        return (
          <Typography key={menu.id} variant="h6" color="error" align="center">
            Menu Items Error
          </Typography>
        )
    }
  })

  return (
    <List
      sx={{ px: 0 }}
      subheader={
        item.title && (
          <ListSubheader
            disableSticky
            sx={{
              ...theme.typography.labelMono,
              color: theme.vars.palette.onSurfaceVariant,
              bgcolor: 'transparent',
              px: 1.5,
              py: 1,
              lineHeight: 1,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontSize: '10px',
            }}
          >
            {item.title}
          </ListSubheader>
        )
      }
    >
      {items}
    </List>
  )
}

export default NavGroup
