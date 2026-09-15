import {
  Bell,
  Command,
  ExternalLink,
  Languages,
  Map,
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
import { OperationsRoutes, operationsRoutes } from "./routes";

const operationsNavigation = [
  { label: "Video operations", routes: operationsRoutes.slice(0, 4) },
  { label: "Platform control", routes: operationsRoutes.slice(4, 9) },
  { label: "Reliability", routes: operationsRoutes.slice(9) },
] as const;

const operationsSearchItems = operationsNavigation.flatMap((group) =>
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
    <div className="operations-shell">
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
        <PortalSwitcher current="operations" />
        <button className="global-search" type="button" onClick={() => setSearchOpen(true)}>
          <Search size={16} />
          <span>Search cameras and workspaces</span>
        </button>
        <div className="header-actions">
          <IconButton label="Open operations search" onClick={() => setSearchOpen(true)}>
            <Command size={18} />
          </IconButton>
          <a
            className="icon-link"
            href="http://127.0.0.1:4174/gis"
            aria-label="Open GIS Center"
            title="Open GIS Center"
          >
            <Map size={18} />
          </a>
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
            aria-controls="operations-navigation"
            onClick={() => setNavOpen((value) => !value)}
          >
            <Menu size={18} />
          </IconButton>
        </div>
      </header>
      <div className="generated-banner" role="status">
        <ShieldCheck size={14} />
        <span>Generated environment. No operational data.</span>
        <small>View-only controls.</small>
      </div>
      <aside id="operations-navigation" className={navOpen ? "side-nav open" : "side-nav"}>
        <nav aria-label="Operations navigation">
          {operationsNavigation.map((group) => (
            <NavigationSection key={group.label} label={group.label}>
              {group.routes.map(([path, label]) => (
                <NavLink
                  key={path}
                  to={path}
                  end={path === "/operations"}
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
          <a href="http://127.0.0.1:4174/gis">
            <Map size={17} />
            <span>GIS Center</span>
            <ExternalLink size={14} />
          </a>
          <a href="http://127.0.0.1:4178/admin">
            <Settings2 size={17} />
            <span>Admin Center</span>
            <ExternalLink size={14} />
          </a>
          <a href="http://127.0.0.1:4179/security">
            <ShieldCheck size={17} />
            <span>Security Center</span>
            <ExternalLink size={14} />
          </a>
        </div>
        <div className="session-block">
          <span>Department</span>
          <strong>{session.department.label}</strong>
          <span>Authority</span>
          <strong>Generated view only</strong>
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
          <span>OPERATIONS / GENERATED</span>
          <span>
            <Languages size={14} /> EN
          </span>
          <span className="status-current">Current projection</span>
        </div>
        <OperationsRoutes />
      </main>
      {searchOpen ? (
        <WorkspaceCommandPalette
          title="Operations navigation"
          placeholder="Search cameras, services, capacity..."
          boundary="Navigate generated operations views. Live controls remain view-only."
          items={operationsSearchItems}
          onClose={() => setSearchOpen(false)}
        />
      ) : null}
    </div>
  );
}
