import {
  Bell,
  Command,
  ExternalLink,
  FileSearch,
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
import { InvestigationRoutes, investigationRoutes } from "./routes";

const investigationNavigation = [
  { label: "Investigations", routes: investigationRoutes.slice(0, 2) },
  { label: "Analysis", routes: investigationRoutes.slice(2, 5) },
  { label: "Relationships", routes: [investigationRoutes[6], investigationRoutes[7]] },
  {
    label: "Governance",
    routes: [investigationRoutes[5], investigationRoutes[8], investigationRoutes[9]],
  },
] as const;

const investigationSearchItems = investigationNavigation.flatMap((group) =>
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
    document.title = "Investigation Center | NETRA SENTINEL";
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
    <div className="investigation-shell">
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
        <PortalSwitcher current="investigations" />
        <button className="global-search" type="button" onClick={() => setSearchOpen(true)}>
          <Search size={16} />
          <span>Search generated records</span>
        </button>
        <div className="header-actions">
          <IconButton label="Open investigation search" onClick={() => setSearchOpen(true)}>
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
            aria-controls="investigation-navigation"
            onClick={() => setNavOpen((value) => !value)}
          >
            <Menu size={18} />
          </IconButton>
        </div>
      </header>
      <div className="generated-banner" role="status">
        <ShieldCheck size={14} />
        <span>Generated environment. No source or evidence is resolved.</span>
        <small>Record sequence is authoritative.</small>
      </div>
      <aside
        id="investigation-navigation"
        aria-label="Investigation workspace sidebar"
        className={navOpen ? "side-nav open" : "side-nav"}
      >
        <nav aria-label="Investigation navigation">
          {investigationNavigation.map((group) => (
            <NavigationSection key={group.label} label={group.label}>
              {group.routes.map(([path, label]) => (
                <NavLink
                  key={path}
                  to={path}
                  end={path === "/investigations"}
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
          <a href="http://127.0.0.1:4175/intelligence">
            <FileSearch size={17} />
            <span>Intelligence Center</span>
            <ExternalLink size={14} />
          </a>
          <a href="http://127.0.0.1:4177/evidence">
            <FolderClock size={17} />
            <span>Evidence Desk</span>
            <ExternalLink size={14} />
          </a>
        </div>
        <div className="session-block">
          <span>Department</span>
          <strong>{session.department.label}</strong>
          <span>Purpose</span>
          <strong>Generated review</strong>
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
          <span>INVESTIGATIONS / GENERATED</span>
          <span>
            <Languages size={14} /> EN
          </span>
          <span className="status-current">HTTP-confirmed projection</span>
        </div>
        <InvestigationRoutes />
      </main>
      {searchOpen ? (
        <WorkspaceCommandPalette
          title="Investigation navigation"
          placeholder="Search timelines, reconstruction, evidence..."
          boundary="Navigate generated investigation views. Source references remain unresolved."
          items={investigationSearchItems}
          onClose={() => setSearchOpen(false)}
        />
      ) : null}
    </div>
  );
}
