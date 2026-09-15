import { PlatformOperationsPageFrame } from "../components/platform-operations-state-boundary";
import { SloBudgetPanel } from "../components/slo-budget-panel";
export function SloErrorBudgetPage() {
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / RELIABILITY"
      title="SLO and error budgets"
      description="Generated objectives support workflow validation but are not selected production targets, measured service levels, or hardware-capacity claims."
    >
      <SloBudgetPanel />
    </PlatformOperationsPageFrame>
  );
}
