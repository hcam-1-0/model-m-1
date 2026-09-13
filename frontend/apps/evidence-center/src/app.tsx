import {
  Bell,
  Command,
  ExternalLink,
  FileLock2,
  FolderClock,
  Languages,
  Menu,
  Moon,
  Search,
  ShieldCheck,
  Sun,
  UserRound,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink } from "react-router";
import { generatedSession } from "@hcam/test-fixtures";
import {
  IconButton,
  NavigationSection,
  PortalSwitcher,
  RouteGlyph,
  WorkspaceCommandPalette,
} from "@hcam/ui";
import { EvidenceRoutes, evidenceRoutes } from "./routes";

const evidenceNavigation = [
  { label: "Evidence desk", routes: evidenceRoutes.slice(0, 2) },
  { label: "Integrity and lineage", routes: evidenceRoutes.slice(2, 4) },
  { label: "Governance", routes: evidenceRoutes.slice(4) },
] as const;

const evidenceSearchItems = evidenceNavigation.flatMap((group) =>
  group.routes.map(([href, label]) => ({ href, label, group: group.label })),
);

export function App() {
  const [navOpen, setNavOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const session = generatedSession();
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  useEffect(() => {
    document.title = "Evidence Desk | NETRA SENTINEL";
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
      }
      if (event.key === "Escape") {
        setSearchOpen(false);
        setNavOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  return (
    <div className="evidence-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="global-header">
        <a
          className="brand"
          href="http://127.0.0.1:4173/command"
          aria-label="NETRA SENTINEL Command Center"
        >
          <ShieldCheck size={23} />
          <span>
            <strong>NETRA</strong>
            <small>SENTINEL</small>
          </span>
        </a>
        <PortalSwitcher current="evidence" />
        <button className="global-search" type="button" onClick={() => setSearchOpen(true)}>
          <Search size={16} />
          <span>Search generated references</span>
        </button>
        <div className="header-actions">
          <IconButton label="Open evidence search" onClick={() => setSearchOpen(true)}>
            <Command size={18} />
          </IconButton>
          <IconButton label="Generated notifications">
            <Bell size={18} />
          </IconButton>
          <IconButton
            label="Change theme"
            onClick={() => setTheme((value) => (value === "light" ? "dark" : "light"))}
          >
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
          </IconButton>
          <IconButton label="Session">
            <UserRound size={18} />
          </IconButton>
          <IconButton
            className="mobile-menu"
            label={navOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={navOpen}
            aria-controls="evidence-navigation"
            onClick={() => setNavOpen((value) => !value)}
          >
            <Menu size={18} />
          </IconButton>
        </div>
      </header>
      <div className="generated-banner" role="status">
        <FileLock2 size={14} />
        <span>Generated references only. Source content is never resolved.</span>
        <small>Evidence operations are disabled.</small>
      </div>
      <aside
        id="evidence-navigation"
        aria-label="Evidence workspace sidebar"
        className={navOpen ? "side-nav open" : "side-nav"}
      >
        <nav aria-label="Evidence navigation">
          {evidenceNavigation.map((group) => (
            <NavigationSection key={group.label} label={group.label}>
              {group.routes.map(([path, label]) => (
                <NavLink
                  key={path}
                  to={path}
                  end={path === "/evidence"}
                  onClick={() => setNavOpen(false)}
                >
                  <RouteGlyph path={path} />
                  <span>{label}</span>
                </NavLink>
              ))}
            </NavigationSection>
          ))}
        </nav>
        <div className="linked-centers">
          <a href="http://127.0.0.1:4173/command">
            <ShieldCheck size={17} />
            <span>Command Center</span>
            <ExternalLink size={14} />
          </a>
          <a href="http://127.0.0.1:4176/investigations">
            <FolderClock size={17} />
            <span>Investigation Center</span>
            <ExternalLink size={14} />
          </a>
        </div>
        <div className="session-block">
          <span>Department</span>
          <strong>{session.department.label}</strong>
          <span>Capability</span>
          <strong>Evidence viewer</strong>
        </div>
      </aside>
      {navOpen ? (
        <button
          className="nav-backdrop"
          type="button"
          aria-label="Close navigation"
          onClick={() => setNavOpen(false)}
        />
      ) : null}
      <main id="main-content" tabIndex={-1}>
        <div className="workspace-meta">
          <span>EVIDENCE / GENERATED REFERENCES</span>
          <span>
            <Languages size={14} /> EN
          </span>
          <span className="status-current">Source boundary enforced</span>
        </div>
        <EvidenceRoutes />
      </main>
      {searchOpen ? (
        <WorkspaceCommandPalette
          title="Evidence navigation"
          placeholder="Search integrity, provenance, policy..."
          boundary="Navigate generated evidence views. Source content is never resolved."
          items={evidenceSearchItems}
          onClose={() => setSearchOpen(false)}
        />
      ) : null}
    </div>
  );
}
