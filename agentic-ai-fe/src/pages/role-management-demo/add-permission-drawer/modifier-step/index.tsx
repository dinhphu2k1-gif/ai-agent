import { ResourceType } from '../../types'
import type { ResourceNode, RowFilterConfig, ColumnMaskConfig } from '../../types'
import ColumnMaskSection from './column-mask/ColumnMaskSection'
import RowFilterSection from './RowFilterSection'
import NoModifierSection from './NoModifierSection'

interface ModifierStepProps {
  resourceType: ResourceType | null
  selectedPath: ResourceNode[] | null
  onGoToStep: (step: number) => void
  rowFilter: RowFilterConfig
  onChangeRowFilter: (patch: Partial<RowFilterConfig>) => void
  columnMask: ColumnMaskConfig
  onChangeColumnMask: (patch: Partial<ColumnMaskConfig>) => void
}

const ModifierStep = (props: ModifierStepProps) => {
  if (props.resourceType === ResourceType.Column) {
    return (
      <ColumnMaskSection
        columnMaskEnabled={props.columnMask.enabled}
        onChangeColumnMaskEnabled={(v) => props.onChangeColumnMask({ enabled: v })}
        maskType={props.columnMask.maskType}
        onChangeMaskType={(v) => props.onChangeColumnMask({ maskType: v })}
        maskPattern={props.columnMask.maskPattern}
        onChangeMaskPattern={(v) => props.onChangeColumnMask({ maskPattern: v })}
        testValue={props.columnMask.testValue}
        onChangeTestValue={(v) => props.onChangeColumnMask({ testValue: v })}
      />
    )
  }

  if (props.resourceType === ResourceType.Table) {
    return (
      <RowFilterSection
        rowFilterEnabled={props.rowFilter.enabled}
        onChangeRowFilterEnabled={(v) => props.onChangeRowFilter({ enabled: v })}
        conditionExpression={props.rowFilter.conditionExpression}
        onChangeConditionExpression={(v) => props.onChangeRowFilter({ conditionExpression: v })}
      />
    )
  }

  // Schema & Database empty state modifier matching step3.2.html
  return (
    <NoModifierSection selectedPath={props.selectedPath} onGoToStep={props.onGoToStep} />
  )
}

export default ModifierStep
