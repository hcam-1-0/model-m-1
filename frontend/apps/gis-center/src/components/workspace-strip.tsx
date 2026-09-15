import { CopyPlus, Save, Share2 } from "lucide-react";
export function WorkspaceStrip() {
  return (
    <div className="workspace-strip">
      <span>
        Workspace <strong>Generated city overview</strong>
      </span>
      <button type="button" disabled>
        <Save size={15} />
        Save disabled
      </button>
      <button type="button" disabled>
        <Share2 size={15} />
        Share disabled
      </button>
      <a href="http://127.0.0.1:4174/gis" target="_blank" rel="noreferrer">
        <CopyPlus size={15} />
        New display window
      </a>
    </div>
  );
}
