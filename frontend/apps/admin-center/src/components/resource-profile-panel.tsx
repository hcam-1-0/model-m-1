import { Cpu } from "lucide-react";
import { profileProjections } from "../data/admin-projections";
export function ResourceProfilePanel() {
  return (
    <section className="panel wide">
      <header>
        <div>
          <span className="eyebrow">DYNAMIC PRESENTATION</span>
          <h2>Resource profiles</h2>
        </div>
        <Cpu size={20} />
      </header>
      <div className="profile-grid">
        {profileProjections.map((profile) => (
          <article key={profile.profile}>
            <strong>{profile.profile.replaceAll("_", " ")}</strong>
            <span>{profile.visualization.replaceAll("_", " ")}</span>
            <small>
              {profile.rowLimit} rows / {profile.refreshSeconds}s
            </small>
            <em>Authority unchanged</em>
          </article>
        ))}
      </div>
    </section>
  );
}
