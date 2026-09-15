import { LockKeyhole } from "lucide-react";
export function NonEffectiveControl({
  label,
  detail,
}: {
  readonly label: string;
  readonly detail: string;
}) {
  return (
    <div className="non-effective-control">
      <div>
        <LockKeyhole size={17} />
        <span>
          <strong>{label}</strong>
          <small>{detail}</small>
        </span>
      </div>
      <button type="button" disabled>
        Unavailable
      </button>
    </div>
  );
}
