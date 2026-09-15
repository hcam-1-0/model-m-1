import {
  Bell,
  Command,
  ExternalLink,
  Languages,
  LockKeyhole,
  Menu,
  Moon,
  Search,
  Settings2,
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
import { SecurityRoutes, securityRoutes } from "./routes";

const securityNavigation = [
  { label: "Security posture", routes: securityRoutes.slice(0, 2) },
  { label: "Activity", routes: securityRoutes.slice(2, 6) },
  { label: "Assurance", routes: securityRoutes.slice(6) },
] as const;

const securitySearchItems = securityNavigation.flatMap((group) =>
  group.routes.map(([href, label]) => ({ href, label, group: group.label })),
);

export function App() {
  const [navOpen, setNavOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const session = generatedSession();
  useEffect(() => {
    document.title = "Security Center | NETRA SENTINEL";
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  useEffect(() => {
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
    <div className="security-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="global-header">
        <div className="brand">
          <ShieldCheck size={23} />
          <span>
            <strong>NETRA</strong>
            <small>SENTINEL</small>
          </span>
        </div>
        <PortalSwitcher current="security" />
        <button className="global-search" type="button" onClick={() => setSearchOpen(true)}>
          <Search size={16} />
          <span>Search assurance records</span>
        </button>
        <div className="header-actions">
          <IconButton label="Open security search" onClick={() => setSearchOpen(true)}>
            <Command size={18} />
          </IconButton>
          <IconButton label="Notifications">
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
            aria-controls="security-navigation"
            onClick={() => setNavOpen((value) => !value)}
          >
            <Menu size={18} />
          </IconButton>
        </div>
      </header>
      <div className="generated-banner" role="status">
        <ShieldCheck size={14} />
        <span>Generated assurance environment. No live security telemetry.</span>
        <small>Raw payloads are not retained.</small>
      </div>
      <aside id="security-navigation" className={navOpen ? "side-nav open" : "side-nav"}>
        <nav aria-label="Security navigation">
          {securityNavigation.map((group) => (
            <NavigationSection key={group.label} label={group.label}>
              {group.routes.map(([path, label]) => (
                <NavLink
                  key={path}
                  to={path}
                  end={path === "/security"}
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
          <a href="http://127.0.0.1:4178/admin">
            <Settings2 size={17} />
            <span>Admin Center</span>
            <ExternalLink size={14} />
          </a>
          <a href="http://127.0.0.1:4180/operations/platform">
            <LockKeyhole size={17} />
            <span>Operations Center</span>
            <ExternalLink size={14} />
          </a>
        </div>
        <div className="session-block">
          <span>Department</span>
          <strong>{session.department.label}</strong>
          <span>Authority</span>
          <strong>Generated security viewer</strong>
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
          <span>SECURITY / GENERATED</span>
          <span>
            <Languages size={14} /> EN
          </span>
          <span className="status-current">Qualified projection</span>
        </div>
        <SecurityRoutes />
      </main>
      {searchOpen ? (
        <WorkspaceCommandPalette
          title="Security navigation"
          placeholder="Search access, audit, supply chain..."
          boundary="Navigate generated assurance views. No live security telemetry is connected."
          items={securitySearchItems}
          onClose={() => setSearchOpen(false)}
        />
      ) : null}
    </div>
  );
}
