import { RuleTrace } from "../components/rule-trace";
import { ruleTrace } from "../data/intelligence-projections";
export function RuleEvaluationsPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS / RULES</p>
          <h1>Rule evaluations</h1>
          <p>
            Exact revisioned inputs, typed temporal and geometry steps, visible abstention, and
            declared limitations.
          </p>
        </div>
        <span className="page-icon">revision {ruleTrace.ruleRevision}</span>
      </header>
      <RuleTrace trace={ruleTrace} />
    </>
  );
}
