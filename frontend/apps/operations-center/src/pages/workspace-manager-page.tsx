import { Copy, LayoutGrid, LockKeyhole, Plus } from "lucide-react";
import { useState } from "react";
import { updateLayout, type WorkspaceLayout } from "@hcam/camera-live-domain";
import { generatedLayout } from "@hcam/test-fixtures";

export function WorkspaceManagerPage() {
  const [layout, setLayout] = useState<WorkspaceLayout>(() => generatedLayout(4));
  const [message, setMessage] = useState("Current generated revision");
  const updateColumns = (columns: 1 | 2 | 3 | 4) => {
    const next = {
      ...layout,
      columns,
      revision: layout.revision + 1,
      etag: `SYN-ETAG-${String(layout.revision + 1).padStart(4, "0")}`,
    };
    const result = updateLayout(layout, layout.etag, next);
    setLayout(result.layout);
    setMessage(
      result.accepted ? "Generated revision updated" : "Layout conflict; refresh required",
    );
  };
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">OPERATIONS / WORKSPACES</p>
          <h1>Workspace manager</h1>
          <p>
            Generated layout preferences with optimistic concurrency and no operational camera
            control.
          </p>
        </div>
        <button className="primary-button" type="button" disabled>
          <Plus size={16} /> New workspace
        </button>
      </header>
      <section className="workspace-list">
        <article className="workspace-record">
          <header>
            <div>
              <LayoutGrid size={19} />
              <div>
                <strong>{layout.name}</strong>
                <small>{layout.id}</small>
              </div>
            </div>
            <span className="truth current">revision {layout.revision}</span>
          </header>
          <div
            className="workspace-preview"
            style={{ "--preview-columns": layout.columns } as React.CSSProperties}
          >
            {layout.tiles.map((tile) => (
              <span key={tile.tileId}>{tile.order + 1}</span>
            ))}
          </div>
          <footer>
            <span role="status">{message}</span>
            <div className="segmented" aria-label="Layout columns">
              {([1, 2, 3, 4] as const).map((columns) => (
                <button
                  key={columns}
                  type="button"
                  aria-pressed={layout.columns === columns}
                  onClick={() => updateColumns(columns)}
                >
                  {columns}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="icon-command"
              title="Duplicate generated layout"
              aria-label="Duplicate generated layout"
            >
              <Copy size={16} />
            </button>
          </footer>
        </article>
        <aside className="policy-aside">
          <LockKeyhole size={20} />
          <h2>Preference boundary</h2>
          <p>
            Layouts contain generated stream references only. They cannot grant playback, change
            camera configuration, or expand department authority.
          </p>
          <dl>
            <div>
              <dt>Maximum tiles</dt>
              <dd>10</dd>
            </div>
            <div>
              <dt>Conflict control</dt>
              <dd>ETag</dd>
            </div>
            <div>
              <dt>Persistence</dt>
              <dd>Generated fixture</dd>
            </div>
          </dl>
        </aside>
      </section>
    </>
  );
}
