import { Drawer, Box, Typography, IconButton, Button } from '@mui/material'
import { usePermissionForm } from './hooks/usePermissionForm'
import PermissionStepper from './components/PermissionStepper'
import ContextBar from './components/ContextBar'
import ResourceStep from './resource-step'
import ActionEffectStep from './action-effect-step'
import ModifierStep from './modifier-step'
import ReviewStep from './review-step'

interface AddPermissionDrawerProps {
  open: boolean
  onClose: () => void
  roleName?: string
}

const AddPermissionDrawer = ({ open, onClose, roleName = 'analyst' }: AddPermissionDrawerProps) => {
  const form = usePermissionForm(open)

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
      {/* Header */}
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
            Add permission
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
              person
            </span>
            <Typography variant="labelMono">{roleName}</Typography>
          </Box>
        </Box>
        <IconButton onClick={onClose} size="small" sx={{ color: 'onSurfaceVariant' }}>
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      {/* Stepper */}
      <PermissionStepper steps={form.steps} activeStep={form.activeStep} />

      {/* Persistent Context Bar */}
      {form.activeStep > 0 && form.selectedPath && form.targetNode && (
        <ContextBar
          selectedPath={form.selectedPath}
          resourceType={form.resourceType}
          targetNode={form.targetNode}
        />
      )}

      {/* Body */}
      <Box
        sx={{
          flex: 1,
          overflow: form.activeStep === 0 ? 'hidden' : 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          bgcolor: 'surface',
        }}
      >
        {form.activeStep === 0 && (
          <ResourceStep
            selectedPath={form.selectedPath}
            roleName={roleName}
            onSelect={(_node, path) => form.setSelectedPath(path)}
            onClear={() => form.setSelectedPath(null)}
          />
        )}

        {form.activeStep === 1 && (
          <ActionEffectStep
            selectedActions={form.selectedActions}
            onChangeActions={form.setSelectedActions}
            effect={form.effect}
            onChangeEffect={form.setEffect}
          />
        )}

        {form.activeStep === 2 && (
          <ModifierStep
            resourceType={form.resourceType}
            selectedPath={form.selectedPath}
            onGoToStep={form.setStep}
            rowFilter={form.rowFilter}
            onChangeRowFilter={form.onChangeRowFilter}
            columnMask={form.columnMask}
            onChangeColumnMask={form.onChangeColumnMask}
          />
        )}

        {form.activeStep === 3 && (
          <ReviewStep
            roleName={roleName}
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

      {/* Footer */}
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
          disabled={!form.isStepValid}
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
            ? 'Grant permission'
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
