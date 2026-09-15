import { ArrowRight, FileClock, FolderSearch, ShieldCheck } from "lucide-react";
import { Link } from "react-router";
import { AuthorityLimit } from "../components/authority-limit";
import { WorkloadStrip } from "../components/workload-strip";
import { investigationQueue, producerGaps } from "../data/investigation-projections";
export function InvestigationOverviewPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">OPERATIONS / INVESTIGATION RECORDS</p>
          <h1>Investigation overview</h1>
          <p>
            Generated, append-only investigation chronology with exact revision reconstruction and
            independently authorized evidence references.
          </p>
        </div>
        <Link className="primary-link" to="/investigations/queue">
          <FolderSearch size={16} /> Open investigation queue
        </Link>
      </header>
      <WorkloadStrip />
      <div className="overview-grid">
        <section className="panel table-panel">
          <header>
            <div>
              <span className="eyebrow">SERVER-ORDERED WORK</span>
              <h2>Active generated investigations</h2>
            </div>
            <Link to="/investigations/queue">
              View queue <ArrowRight size={15} />
            </Link>
          </header>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Investigation</th>
                  <th>State</th>
                  <th>Records</th>
                  <th>Evidence</th>
                  <th>Freshness</th>
                  <th>
                    <span className="sr-only">Open</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {investigationQueue.items.slice(0, 6).map((item) => (
                  <tr key={item.ref}>
                    <td>
                      <strong>{item.title}</strong>
                      <code>{item.ref}</code>
                    </td>
                    <td>
                      <span className={`status-chip status-${item.state}`}>
                        {item.state.replaceAll("_", " ")}
                      </span>
                    </td>
                    <td>
                      {item.timelineEntries}
                      <small>seq {item.latestRecordSequence}</small>
                    </td>
                    <td>
                      {item.evidenceReferences}
                      <small>references only</small>
                    </td>
                    <td>
                      {item.freshness.completeness}
                      <small>{item.freshness.observedAt.slice(11, 16)}</small>
                    </td>
                    <td>
                      <Link
                        className="row-link"
                        to={`/investigations/${item.ref}`}
                        aria-label={`Open ${item.title}`}
                      >
                        <ArrowRight size={15} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <section className="panel record-principles">
          <header>
            <div>
              <span className="eyebrow">CHRONOLOGY CONTROL</span>
              <h2>Record authority</h2>
            </div>
            <FileClock size={19} />
          </header>
          <ol>
            <li>
              <ShieldCheck size={15} />
              <div>
                <strong>Record sequence</strong>
                <span>Authoritative durable ordering</span>
              </div>
            </li>
            <li>
              <FileClock size={15} />
              <div>
                <strong>Event-time context</strong>
                <span>Qualified by precision and clock state</span>
              </div>
            </li>
            <li>
              <FolderSearch size={15} />
              <div>
                <strong>Exact reconstruction</strong>
                <span>Revision, digest, omissions, limitations</span>
              </div>
            </li>
          </ol>
          <footer>{producerGaps.length} producer contracts remain unavailable.</footer>
        </section>
      </div>
      <AuthorityLimit />
    </>
  );
}
