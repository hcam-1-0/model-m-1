import { LayoutGrid, RotateCcw } from "lucide-react";
import type { ResourceProfileId } from "@hcam/camera-live-domain";
import { generatedProfiles } from "@hcam/test-fixtures";

export function WorkspaceToolbar({
  profile,
  columns,
  onProfile,
  onColumns,
  onReset,
}: {
  readonly profile: ResourceProfileId;
  readonly columns: number;
  readonly onProfile: (profile: ResourceProfileId) => void;
  readonly onColumns: (columns: 1 | 2 | 3 | 4) => void;
  readonly onReset: () => void;
}) {
  return (
    <div className="workspace-toolbar">
      <label>
        <span>Resource profile</span>
        <select
          value={profile}
          onChange={(event) => onProfile(event.target.value as ResourceProfileId)}
        >
          {generatedProfiles.map((value) => (
            <option key={value} value={value}>
              {value.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>
      <div className="segmented" aria-label="Workspace columns">
        {([1, 2, 3, 4] as const).map((value) => (
          <button
            key={value}
            type="button"
            aria-pressed={columns === value}
            onClick={() => onColumns(value)}
          >
            <LayoutGrid size={14} /> {value}
          </button>
        ))}
      </div>
      <button
        className="icon-command"
        type="button"
        onClick={onReset}
        title="Reset generated layout"
      >
        <RotateCcw size={16} />
        <span className="sr-only">Reset generated layout</span>
      </button>
    </div>
  );
}
