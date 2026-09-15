import { ArrowLeft, Command, Menu, Moon, ShieldCheck, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink } from "react-router";
import {
  IconButton,
  NavigationSection,
  PortalSwitcher,
  RouteGlyph,
  WorkspaceCommandPalette,
} from "@hcam/ui";
import { gisRoutes, GisRoutes } from "./routes";
import { isLoopbackHostname } from "./map-runtime";

const gisNavigation = [
  { label: "Spatial operations", routes: [gisRoutes[0], gisRoutes[1], gisRoutes[5]] },
  { label: "Coverage and layers", routes: gisRoutes.slice(2, 5) },
  { label: "Coordination", routes: gisRoutes.slice(6) },
] as const;

const gisSearchItems = gisNavigation.flatMap((group) =>
  group.routes.map(([href, label]) => ({ href, label, group: group.label })),
);

export function App() {
  const [open, setOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const developmentBasemapActive = isLoopbackHostname(window.location.hostname);
  useEffect(() => {
    document.title = "GIS Center | NETRA SENTINEL";
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
        setOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  return (
    <div className="gis-shell">
      <a className="skip-link" href="#gis-main">
        Skip to GIS workspace
      </a>
      <header className="gis-header">
        <div className="gis-brand">
          <ShieldCheck size={22} />
          <span>
            <strong>NETRA SENTINEL</strong>
            <small>GIS CENTER</small>
          </span>
        </div>
        <PortalSwitcher current="gis" />
        <button className="gis-search-button" type="button" onClick={() => setSearchOpen(true)}>
          <Command size={17} aria-hidden="true" />
          <span>Find a GIS view</span>
          <kbd>Ctrl K</kbd>
        </button>
        <IconButton
          label="Change theme"
          onClick={() => setTheme((value) => (value === "light" ? "dark" : "light"))}
        >
          {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
        </IconButton>
        <a className="command-return" href="http://127.0.0.1:4173/command">
          <ArrowLeft size={16} />
          Command Center
        </a>
        <button
          className="menu-button"
          type="button"
          aria-label={open ? "Close GIS navigation" : "Open GIS navigation"}
          aria-expanded={open}
          aria-controls="gis-navigation"
          onClick={() => setOpen(!open)}
        >
          <Menu size={18} />
        </button>
      </header>
      <section className="gis-notice" aria-label="Generated environment status">
        <ShieldCheck size={14} />
        {developmentBasemapActive
          ? "Public development basemap active. Camera and alert overlays remain generated."
          : "Generated local geography. No provider, tile, camera, or operational network access."}
      </section>
      <aside
        id="gis-navigation"
        aria-label="GIS portal navigation"
        className={open ? "gis-nav open" : "gis-nav"}
      >
        <nav aria-label="GIS Center navigation">
          {gisNavigation.map((group) => (
            <NavigationSection key={group.label} label={group.label}>
              {group.routes.map(([path, label]) => (
                <NavLink key={path} to={path} end={path === "/gis"} onClick={() => setOpen(false)}>
                  <RouteGlyph path={path} />
                  <span>{label}</span>
                </NavLink>
              ))}
            </NavigationSection>
          ))}
        </nav>
        <div className="gis-boundary">
          <span>RESOURCE PROFILE</span>
          <strong>Adaptive renderer</strong>
          <span>AUTHORITATIVE FALLBACK</span>
          <strong>List and table active</strong>
        </div>
      </aside>
      {open ? (
        <button
          className="nav-backdrop"
          type="button"
          aria-label="Close GIS navigation"
          onClick={() => setOpen(false)}
        />
      ) : null}
      <main id="gis-main" tabIndex={-1}>
        <GisRoutes />
      </main>
      {searchOpen ? (
        <WorkspaceCommandPalette
          title="GIS navigation"
          placeholder="Search maps, coverage, layers, movement..."
          boundary="Navigate generated spatial views. Development basemap access never enables camera or operational networks."
          items={gisSearchItems}
          onClose={() => setSearchOpen(false)}
        />
      ) : null}
    </div>
  );
}
