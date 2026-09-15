import { Database, LockKeyhole, RadioTower } from "lucide-react";
export function SourceStatus() {
  return (
    <section className="gis-status" aria-label="GIS source status">
      <span>
        <Database size={15} />
        <small>Projection</small>
        <strong>SYN-REV-P5-2-001</strong>
      </span>
      <span>
        <RadioTower size={15} />
        <small>External sources</small>
        <strong>Disabled</strong>
      </span>
      <span>
        <LockKeyhole size={15} />
        <small>Department</small>
        <strong>SYN-DEPT-01</strong>
      </span>
    </section>
  );
}
