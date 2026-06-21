import { Chip, styled } from '@mui/material'
import type {
  PermissionAction,
  PermissionEffect,
  PermissionModifier,
} from '@/pages/role-management/types'

const chipBase = {
  height: 20,
  fontSize: 10,
  fontWeight: 600,
  fontFamily: 'JetBrains Mono, monospace',
  letterSpacing: '0.02em',
  '& .MuiChip-label': { px: 1 },
}

const EffectChip = styled(Chip, {
  shouldForwardProp: (prop) => prop !== 'effect',
})<{ effect: PermissionEffect }>(({ effect }) => ({
  ...chipBase,
  borderRadius: effect === 'ALLOW' ? 9999 : 4,
  ...(effect === 'ALLOW'
    ? {
      backgroundColor: 'var(--mui-palette-statusActiveBg)',
      color: 'var(--mui-palette-statusActiveText)',
      border: '1px solid var(--mui-palette-statusActiveBorder)',
    }
    : {
      backgroundColor: 'color-mix(in srgb, var(--mui-palette-error-main) 10%, transparent)',
      color: 'var(--mui-palette-error-main)',
      border: '1px solid color-mix(in srgb, var(--mui-palette-error-main) 20%, transparent)',
    }),
}))

const ActionChip = styled(Chip)(() => ({
  ...chipBase,
  borderRadius: 4,
  backgroundColor: 'color-mix(in srgb, var(--mui-palette-tertiary) 10%, transparent)',
  color: 'var(--mui-palette-tertiary)',
  border: '1px solid color-mix(in srgb, var(--mui-palette-tertiary) 20%, transparent)',

}))

const ModifierChip = styled(Chip, {
  shouldForwardProp: (prop) => prop !== 'modifierType',
})<{ modifierType: PermissionModifier['type'] }>(({ modifierType }) => ({
  ...chipBase,
  borderRadius: 4,
  ...(modifierType === 'ROW_FILTER'
    ? {
      backgroundColor: 'color-mix(in srgb, var(--mui-palette-primary-main) 12%, transparent)',
      color: 'var(--mui-palette-primary-main)',
      border: '1px solid color-mix(in srgb, var(--mui-palette-primary-main) 20%, transparent)',
    }
    : {
      backgroundColor: 'var(--mui-palette-roleViewerBg)',
      color: 'var(--mui-palette-roleViewerText)',
      border: '1px solid var(--mui-palette-roleViewerBorder)',
    }),
}))

interface PermissionChipsProps {
  effect: PermissionEffect
  action: PermissionAction
  modifier?: PermissionModifier
}

const PermissionChips = ({ effect, action, modifier }: PermissionChipsProps) => (
  <>
    <EffectChip label={effect} effect={effect} size="small" />
    <ActionChip label={action} size="small" />
    {modifier && (
      <ModifierChip
        label={modifier.label}
        modifierType={modifier.type}
        size="small"
        icon={
          <span className="material-symbols-outlined" style={{ fontSize: 12 }}>
            {modifier.type === 'ROW_FILTER' ? 'filter_alt' : 'visibility_off'}
          </span>
        }
      />
    )}
  </>
)

export default PermissionChips
