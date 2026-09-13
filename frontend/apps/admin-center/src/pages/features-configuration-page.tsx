import { SlidersHorizontal } from "lucide-react";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { NonEffectiveControl } from "../components/non-effective-control";
import { configurationProposals } from "../data/admin-projections";
export function FeaturesConfigurationPage() {
  return (
    <AdminPageFrame
      eyebrow="ADMIN / CONFIGURATION"
      title="Features and configuration"
      description="Revisioned proposal records show current, proposed, and impact states; direct toggles and automatic activation do not exist."
    >
      <section className="panel control-list">
        <header>
          <div>
            <span className="eyebrow">GENERATED PROPOSALS</span>
            <h2>Configuration review</h2>
          </div>
          <SlidersHorizontal size={20} />
        </header>
        {configurationProposals.map((item) => (
          <NonEffectiveControl
            key={item.ref}
            label={`${item.kind.replaceAll("_", " ")}: ${item.proposedValue.replaceAll("_", " ")}`}
            detail={`${item.currentValue.replaceAll("_", " ")} current · independent approval required`}
          />
        ))}
      </section>
    </AdminPageFrame>
  );
}
