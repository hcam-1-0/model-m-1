import { Network, ShieldCheck } from "lucide-react";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { SecretReferencePanel } from "../components/secret-reference-panel";
import { providerPosture } from "../data/admin-projections";
export function IntegrationProviderGovernancePage() {
  return (
    <AdminPageFrame
      eyebrow="ADMIN / PROVIDER GOVERNANCE"
      title="Integration and provider governance"
      description="Exact destination-rule, certificate, and opaque secret-reference metadata without provider contact or secret resolution."
    >
      <div className="two-column">
        <section className="panel table-panel">
          <header>
            <div>
              <span className="eyebrow">PROVIDER POSTURE</span>
              <h2>Generated providers</h2>
            </div>
            <Network size={20} />
          </header>
          <div className="table-scroll" tabIndex={0}>
            <table>
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Destination rule</th>
                  <th>Certificate</th>
                  <th>Network</th>
                </tr>
              </thead>
              <tbody>
                {providerPosture.map((item) => (
                  <tr key={item.ref}>
                    <td>
                      <strong>{item.ref}</strong>
                    </td>
                    <td>{item.destinationRuleRef}</td>
                    <td>{item.certificateState}</td>
                    <td>
                      <span className="status blocked">Not contacted</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <div className="detail-stack">
          <SecretReferencePanel />
          <section className="panel">
            <header>
              <div>
                <span className="eyebrow">BOUNDARY</span>
                <h2>Exact destinations only</h2>
              </div>
              <ShieldCheck size={20} />
            </header>
            <p>
              Wildcard, public, redirect, credential-bearing, and unapproved destinations remain
              denied.
            </p>
          </section>
        </div>
      </div>
    </AdminPageFrame>
  );
}
