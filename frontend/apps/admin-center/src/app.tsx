import {
  Bell,
  Command,
  ExternalLink,
  Languages,
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
import { AdminRoutes, adminRoutes } from "./routes";

const adminNavigation = [
  { label: "Organization", routes: adminRoutes.slice(0, 4) },
  { label: "Change control", routes: adminRoutes.slice(4, 7) },
  { label: "Platform policy", routes: adminRoutes.slice(7) },
] as const;

const adminSearchItems = adminNavigation.flatMap((group) =>
  group.routes.map(([href, label]) => ({ href, label, group: group.label })),
);

export function App() {
  const [navOpen, setNavOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const session = generatedSession();
  useEffect(() => {
    document.title = "Admin Center | NETRA SENTINEL";
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
    <div className="admin-shell">
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
        <PortalSwitcher current="admin" />
        <button className="global-search" type="button" onClick={() => setSearchOpen(true)}>
          <Search size={16} />
          <span>Search governance records</span>
        </button>
        <div className="header-actions">
          <IconButton label="Open administration search" onClick={() => setSearchOpen(true)}>
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
            aria-controls="admin-navigation"
            onClick={() => setNavOpen((value) => !value)}
          >
            <Menu size={18} />
          </IconButton>
        </div>
      </header>
      <div className="generated-banner" role="status">
        <ShieldCheck size={14} />
        <span>Generated governance environment. No setting can take effect.</span>
        <small>Independent approval required.</small>
      </div>
      <aside id="admin-navigation" className={navOpen ? "side-nav open" : "side-nav"}>
        <nav aria-label="Administration navigation">
          {adminNavigation.map((group) => (
            <NavigationSection key={group.label} label={group.label}>
              {group.routes.map(([path, label]) => (
                <NavLink
                  key={path}
                  to={path}
                  end={path === "/admin"}
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
          <a href="http://127.0.0.1:4179/security">
            <ShieldCheck size={17} />
            <span>Security Center</span>
            <ExternalLink size={14} />
          </a>
          <a href="http://127.0.0.1:4180/operations/platform">
            <Settings2 size={17} />
            <span>Operations Center</span>
            <ExternalLink size={14} />
          </a>
        </div>
        <div className="session-block">
          <span>Department</span>
          <strong>{session.department.label}</strong>
          <span>Authority</span>
          <strong>Generated administrator</strong>
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
          <span>ADMINISTRATION / GENERATED</span>
          <span>
            <Languages size={14} /> EN
          </span>
          <span className="status-current">HTTP-authoritative projection</span>
        </div>
        <AdminRoutes />
      </main>
      {searchOpen ? (
        <WorkspaceCommandPalette
          title="Administration navigation"
          placeholder="Search users, roles, providers, policies..."
          boundary="Navigate generated governance views. Changes remain non-effective."
          items={adminSearchItems}
          onClose={() => setSearchOpen(false)}
        />
      ) : null}
    </div>
  );
}
