import { Braces } from "lucide-react";
import type { RuleTrace as RuleTraceValue } from "../../../../packages/intelligence-contracts/src";
export function RuleTrace({ trace }: { readonly trace: RuleTraceValue }) {
  return (
    <section className="panel trace-panel">
      <header>
        <div>
          <span className="eyebrow">EXACT REVISIONED TRACE</span>
          <h2>Rule evaluation</h2>
        </div>
        <span>
          <Braces size={16} /> rev {trace.ruleRevision}
        </span>
      </header>
      <div className="trace-meta">
        <span>
          Rule <strong>{trace.ruleRef}</strong>
        </span>
        <span>
          Window <strong>{trace.timerWindow}</strong>
        </span>
        <span>
          Result <strong>{trace.result}</strong>
        </span>
      </div>
      <ol>
        {trace.exactSteps.map((step) => (
          <li key={step.sequence} className={`trace-${step.result}`}>
            <span>{step.sequence}</span>
            <div>
              <strong>{step.label}</strong>
              <small>
                {step.nodeType} / {step.normalizedInput}
              </small>
              {step.limitation ? <p>{step.limitation}</p> : null}
            </div>
            <b>{step.result}</b>
          </li>
        ))}
      </ol>
      <footer>Summaries are subordinate to this exact trace.</footer>
    </section>
  );
}
