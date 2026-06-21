import { Drawer, Box, Typography, IconButton, Button } from '@mui/material'
import { usePermissionForm } from './hooks/usePermissionForm'
import PermissionStepper from './components/PermissionStepper'
import ContextBar from './components/ContextBar'
import ResourceStep from './resource-step'
import ActionEffectStep from './action-effect-step'
import ModifierStep from './modifier-step'
import ReviewStep from './review-step'
import { MOCK_RESOURCES } from './data/mockResourceTree'
import type { AddPermissionDrawerProps } from './types'

const CONTEXT_ICONS: Record<NonNullable<AddPermissionDrawerProps['contextIcon']>, string> = {
  person: 'person',
  groups: 'groups',
  shield: 'shield',
}

const AddPermissionDrawer = ({
  open,
  onClose,
  mode = 'create',
  contextLabel,
  contextIcon = 'shield',
  initialFormState = null,
  onSubmit,
  resourceTree = MOCK_RESOURCES,
  submitDisabled = false,
}: AddPermissionDrawerProps) => {
  const form = usePermissionForm({ open, mode, initialFormState, onSubmit })
  const isEdit = mode === 'edit'
  const showContextBar =
    form.selectedPath && form.targetNode && (isEdit || form.activeStep > 0)

  const submitLabel = isEdit ? 'Save changes' : 'Grant permission'

  return (
    <Drawer
      anchor="right"
      open={open}
      slotProps={{
        paper: {
          sx: {
            width: 480,
            bgcolor: 'surface',
            display: 'flex',
            flexDirection: 'column',
            backgroundImage: 'none',
          },
        },
      }}
    >
      <Box
        sx={{
          px: 3,
          py: 2.5,
          borderBottom: 1,
          borderColor: 'outlineVariant',
          bgcolor: 'surfaceContainerLowest',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Typography variant="displaySm" sx={{ color: 'onSurface' }}>
            {isEdit ? 'Edit permission' : 'Add permission'}
          </Typography>
          <Box
            sx={{
              px: 1.25,
              py: 0.5,
              bgcolor: 'tertiaryContainer',
              color: 'onTertiaryContainer',
              border: 1,
              borderColor: 'tertiaryContainer',
              borderRadius: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
              {CONTEXT_ICONS[contextIcon]}
            </span>
            <Typography variant="labelMono">{contextLabel}</Typography>
          </Box>
        </Box>
        <IconButton onClick={onClose} size="small" sx={{ color: 'onSurfaceVariant' }}>
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      <PermissionStepper steps={form.steps} activeStep={form.activeStep} />

      {showContextBar && (
        <ContextBar
          selectedPath={form.selectedPath!}
          resourceType={form.resourceType}
          targetNode={form.targetNode!}
        />
      )}

      <Box
        sx={{
          flex: 1,
          overflow: form.stepKind === 'resource' ? 'hidden' : 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          bgcolor: 'surface',
        }}
      >
        {form.stepKind === 'resource' && (
          <ResourceStep
            selectedPath={form.selectedPath}
            roleName={contextLabel}
            resources={resourceTree}
            readOnly={form.isResourceLocked}
            onSelect={(_node, path) => form.setSelectedPath(path)}
            onClear={() => form.setSelectedPath(null)}
          />
        )}

        {form.stepKind === 'action' && (
          <ActionEffectStep
            selectedActions={form.selectedActions}
            onChangeActions={form.setSelectedActions}
            effect={form.effect}
            onChangeEffect={form.setEffect}
            selectionMode="single"
          />
        )}

        {form.stepKind === 'modifier' && (
          <ModifierStep
            resourceType={form.resourceType}
            selectedPath={form.selectedPath}
            lockResource={isEdit}
            onGoToStep={form.setStep}
            rowFilter={form.rowFilter}
            onChangeRowFilter={form.onChangeRowFilter}
            columnMask={form.columnMask}
            onChangeColumnMask={form.onChangeColumnMask}
          />
        )}

        {form.stepKind === 'review' && (
          <ReviewStep
            roleName={contextLabel}
            selectedPath={form.selectedPath}
            selectedActions={form.selectedActions}
            effect={form.effect}
            rowFilterEnabled={form.rowFilter.enabled}
            conditionExpression={form.rowFilter.conditionExpression}
            columnMaskEnabled={form.columnMask.enabled}
            maskType={form.columnMask.maskType}
            maskPattern={form.columnMask.maskPattern}
          />
        )}
      </Box>

      <Box
        sx={{
          px: 2,
          py: 1,
          borderTop: 1,
          borderColor: 'outlineVariant',
          bgcolor: 'surfaceContainerLowest',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Button
          onClick={form.activeStep === 0 ? onClose : form.handleBack}
          sx={{ color: 'onSurfaceVariant', textTransform: 'none', typography: 'labelBody' }}
          variant="outlined"
        >
          {form.activeStep === 0 ? 'Cancel' : 'Back'}
        </Button>
        <Button
          variant="contained"
          onClick={form.handleNext}
          disabled={
            (form.activeStep === form.steps.length - 1 ? !form.canSubmit : !form.isStepValid) ||
            submitDisabled
          }
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            typography: 'labelBody',
            borderRadius: 1,
            px: 2,
            py: 1,
          }}
        >
          {form.activeStep === form.steps.length - 1
            ? submitLabel
            : `Next: ${form.steps[form.activeStep + 1]}`}
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
            {form.activeStep === form.steps.length - 1 ? 'verified_user' : 'arrow_forward'}
          </span>
        </Button>
      </Box>
    </Drawer>
  )
}

export default AddPermissionDrawer
