import { Clock3, KeyRound, LockKeyhole } from "lucide-react";
import { SecurityPageFrame } from "../components/security-state-boundary";
const sessions = [
  { ref: "SYN-SESSION-0001", state: "current", factor: "generated_step_up", policy: "R7" },
  {
    ref: "SYN-SESSION-0002",
    state: "reauthentication_required",
    factor: "generated_session",
    policy: "R6",
  },
  { ref: "SYN-SESSION-0003", state: "stale", factor: "unknown", policy: "R5" },
];
export function SessionAuthenticationPage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / SESSION"
      title="Session and authentication assurance"
      description="Generated session freshness, policy revision, and step-up requirements without credentials, tokens, factors, or real identities."
    >
      <section className="summary-band">
        <article>
          <KeyRound size={18} />
          <span>Credentials</span>
          <strong>0</strong>
          <small>Never projected</small>
        </article>
        <article>
          <Clock3 size={18} />
          <span>Sessions</span>
          <strong>{sessions.length}</strong>
          <small>Generated references</small>
        </article>
        <article>
          <LockKeyhole size={18} />
          <span>Break-glass</span>
          <strong>Off</strong>
          <small>Unavailable</small>
        </article>
      </section>
      <section className="panel">
        <div className="table-scroll" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th>Session reference</th>
                <th>State</th>
                <th>Factor class</th>
                <th>Policy</th>
                <th>Token</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((item) => (
                <tr key={item.ref}>
                  <td>
                    <strong>{item.ref}</strong>
                  </td>
                  <td>{item.state.replaceAll("_", " ")}</td>
                  <td>{item.factor.replaceAll("_", " ")}</td>
                  <td>{item.policy}</td>
                  <td>
                    <span className="status blocked">Not available</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </SecurityPageFrame>
  );
}
