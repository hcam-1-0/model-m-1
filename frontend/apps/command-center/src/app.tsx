import {
  Bell,
  Command,
  ExternalLink,
  Languages,
  Map,
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
import { commandRoutes, CommandRoutes } from "./routes";

const commandNavigation = [
  {
    label: "Situational awareness",
    routes: [commandRoutes[0], commandRoutes[1], commandRoutes[2], commandRoutes[3]],
  },
  {
    label: "Coordination",
    routes: [commandRoutes[4], commandRoutes[5], commandRoutes[6], commandRoutes[8]],
  },
  { label: "Platform", routes: [commandRoutes[7], commandRoutes[9]] },
] as const;

const commandSearchItems = commandNavigation.flatMap((group) =>
  group.routes.map(([href, label]) => ({ href, label, group: group.label })),
);

export function App() {
  const [navOpen, setNavOpen] = useState(false);
  const [commandsOpen, setCommandsOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const session = generatedSession();
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandsOpen(true);
      }
      if (event.key === "Escape") {
        setCommandsOpen(false);
        setNavOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  return (
    <div className="ops-shell">
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
        <PortalSwitcher current="command" />
        <button
          className="global-search"
          type="button"
          aria-label="Search generated command views"
          onClick={() => setCommandsOpen(true)}
        >
          <Search size={16} />
          <span>Search generated views</span>
        </button>
        <div className="header-actions">
          <IconButton label="Open command search" onClick={() => setCommandsOpen(true)}>
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
            aria-controls="command-navigation"
            onClick={() => setNavOpen((value) => !value)}
          >
            <Menu size={18} />
          </IconButton>
        </div>
      </header>
      <div className="generated-banner" role="status">
        <ShieldCheck size={14} />
        <span>Generated environment. No operational data.</span>
        <small>Actions disabled.</small>
      </div>
      <aside id="command-navigation" className={navOpen ? "side-nav open" : "side-nav"}>
        <nav aria-label="Primary navigation">
          {commandNavigation.map((group) => (
            <NavigationSection key={group.label} label={group.label}>
              {group.routes.map(([path, label]) => (
                <NavLink
                  key={path}
                  to={path}
                  end={path === "/command"}
                  onClick={() => setNavOpen(false)}
                >
                  <RouteGlyph path={path} />
                  <span>{label}</span>
                </NavLink>
              ))}
            </NavigationSection>
          ))}
        </nav>
        <a className="gis-launch" href="http://127.0.0.1:4174/gis">
          <Map size={17} />
          <span>GIS Center</span>
          <ExternalLink size={14} />
        </a>
        <div className="session-block">
          <span>Department</span>
          <strong>{session.department.label}</strong>
          <span>Profile</span>
          <strong>Adaptive low resource</strong>
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
        <h1 className="sr-only">Command Center</h1>
        <div className="workspace-meta">
          <span>COMMAND / GENERATED</span>
          <span>
            <Languages size={14} /> EN
          </span>
          <span className="status-current">Current snapshot</span>
        </div>
        <CommandRoutes />
      </main>
      {commandsOpen ? (
        <WorkspaceCommandPalette
          title="Command navigation"
          placeholder="Search situation, cameras, workload..."
          boundary="Navigate generated command views. Operational commands remain disabled."
          items={commandSearchItems}
          onClose={() => setCommandsOpen(false)}
        />
      ) : null}
    </div>
  );
}
