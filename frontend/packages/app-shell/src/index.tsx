import {
  Bell,
  Blocks,
  ChevronDown,
  Command,
  Languages,
  Menu,
  Moon,
  Search,
  ShieldCheck,
  Sun,
  UserRound,
  X,
} from "lucide-react";
import { StrictMode, useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import { FormattedMessage, useIntl } from "react-intl";
import { HcamIntlProvider, type Locale } from "@hcam/i18n";
import { portals, type PortalManifest } from "@hcam/navigation";
import { Button, IconButton, Metric, ModalDialog, StateBanner } from "@hcam/ui";
import type { UiState } from "@hcam/contracts";
import "@hcam/design-tokens/styles.css";
import "./styles.css";

export interface PortalRuntimeConfig {
  readonly portal: PortalManifest;
  readonly initialState?: UiState;
}
const activity = [
  { time: "10:04", label: "Generated contract validation", state: "Complete" },
  { time: "10:02", label: "Capability projection refreshed", state: "Current" },
  { time: "09:58", label: "Accessibility invariant check", state: "Complete" },
] as const;

function CommandDialog({ onClose }: { readonly onClose: () => void }) {
  const titleId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    inputRef.current?.focus();
  }, []);
  return (
    <ModalDialog title="Command search" onClose={onClose}>
      <section aria-labelledby={titleId}>
        <header>
          <h2 id={titleId}>Command search</h2>
          <IconButton label="Close command search" onClick={onClose}>
            <X size={18} />
          </IconButton>
        </header>
        <label className="hcam-search">
          <Search size={18} aria-hidden="true" />
          <span className="hcam-visually-hidden">Search available routes</span>
          <input
            ref={inputRef}
            type="search"
            placeholder="Search generated routes"
            autoComplete="off"
          />
        </label>
        <p className="hcam-dialog-note">No operational commands are enabled.</p>
      </section>
    </ModalDialog>
  );
}

function Shell({ config }: { readonly config: PortalRuntimeConfig }) {
  const intl = useIntl();
  const [navOpen, setNavOpen] = useState(false);
  const [commandsOpen, setCommandsOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const state = config.initialState ?? "ready";
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
  useEffect(() => {
    document.title = `${intl.formatMessage({ id: config.portal.titleKey })} | NETRA SENTINEL`;
  }, [config.portal.titleKey, intl]);

  return (
    <div className="hcam-app-shell">
      <a className="hcam-skip-link" href="#main-content">
        <FormattedMessage id="shell.skip" />
      </a>
      <header className="hcam-global-header">
        <div className="hcam-brand">
          <ShieldCheck size={25} aria-hidden="true" />
          <span>
            <strong>NETRA</strong>
            <small>SENTINEL</small>
          </span>
        </div>
        <button
          className="hcam-portal-button"
          type="button"
          aria-label={intl.formatMessage({ id: "shell.portals" })}
        >
          <Blocks size={18} aria-hidden="true" />
          <span>
            <FormattedMessage id={config.portal.titleKey} />
          </span>
          <ChevronDown size={15} aria-hidden="true" />
        </button>
        <div className="hcam-header-actions">
          <IconButton
            label={intl.formatMessage({ id: "shell.command" })}
            onClick={() => setCommandsOpen(true)}
          >
            <Command size={18} />
          </IconButton>
          <IconButton label="Notifications">
            <Bell size={18} />
          </IconButton>
          <IconButton
            label={intl.formatMessage({ id: "shell.theme" })}
            onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}
          >
            {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
          </IconButton>
          <IconButton label={intl.formatMessage({ id: "shell.session" })}>
            <UserRound size={18} />
          </IconButton>
          <IconButton
            className="hcam-mobile-menu"
            label={intl.formatMessage({ id: "shell.menu" })}
            aria-expanded={navOpen}
            onClick={() => setNavOpen((open) => !open)}
          >
            {navOpen ? <X size={18} /> : <Menu size={18} />}
          </IconButton>
        </div>
      </header>
      <div className="hcam-generated-banner" role="status">
        <ShieldCheck size={15} aria-hidden="true" />
        <FormattedMessage id="shell.generated" />
      </div>
      <aside className={`hcam-sidebar${navOpen ? " hcam-sidebar--open" : ""}`}>
        <nav aria-label={intl.formatMessage({ id: "shell.navigation" })}>
          {portals.map((portal) => (
            <a
              key={portal.id}
              href={portal.routeBase}
              aria-current={portal.id === config.portal.id ? "page" : undefined}
              onClick={() => setNavOpen(false)}
            >
              <span className="hcam-nav-indicator" aria-hidden="true" />
              <FormattedMessage id={portal.titleKey} />
            </a>
          ))}
        </nav>
        <div className="hcam-sidebar-footer">
          <span>
            <FormattedMessage id="shell.profile" />
          </span>
          <strong>Low resource</strong>
        </div>
      </aside>
      <main id="main-content" tabIndex={-1}>
        <div className="hcam-page-heading">
          <div>
            <p className="hcam-breadcrumb">
              NETRA SENTINEL / <FormattedMessage id={config.portal.titleKey} />
            </p>
            <h1>
              <FormattedMessage id={config.portal.titleKey} />
            </h1>
          </div>
          <div className="hcam-heading-controls">
            <label>
              <Languages size={16} aria-hidden="true" />
              <span>
                <FormattedMessage id="shell.locale" />
              </span>
              <select
                aria-label={intl.formatMessage({ id: "shell.locale" })}
                value={intl.locale}
                disabled
              >
                <option>{intl.locale.toUpperCase()}</option>
              </select>
            </label>
            <span className="hcam-health">
              <span aria-hidden="true" /> Generated
            </span>
          </div>
        </div>
        <StateBanner
          state={state}
          title={intl.formatMessage({ id: `state.${state}` })}
          detail={intl.formatMessage({ id: "workspace.noActions" })}
          {...(state === "stale" || state === "failure"
            ? {
                action: (
                  <Button>
                    <FormattedMessage id="action.refresh" />
                  </Button>
                ),
              }
            : {})}
        />
        <section className="hcam-metrics" aria-labelledby="overview-title">
          <div className="hcam-section-heading">
            <h2 id="overview-title">
              <FormattedMessage id="workspace.overview" />
            </h2>
            <span>
              <FormattedMessage id="workspace.freshness" />
            </span>
          </div>
          <div className="hcam-metric-grid">
            <Metric
              label={intl.formatMessage({ id: "workspace.review" })}
              value="0"
              status="good"
            />
            <Metric label={intl.formatMessage({ id: "workspace.open" })} value="0" />
            <Metric label={intl.formatMessage({ id: "workspace.coverage" })} value="7" />
            <Metric
              label={intl.formatMessage({ id: "workspace.health" })}
              value="100%"
              status="good"
            />
          </div>
        </section>
        <div className="hcam-workspace-grid">
          <section className="hcam-activity" aria-labelledby="activity-title">
            <div className="hcam-section-heading">
              <h2 id="activity-title">
                <FormattedMessage id="workspace.activity" />
              </h2>
              <Button>
                <FormattedMessage id="action.viewAll" />
              </Button>
            </div>
            <div className="hcam-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Activity</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {activity.map((item) => (
                    <tr key={item.time}>
                      <td>
                        <time>{item.time}</time>
                      </td>
                      <td>{item.label}</td>
                      <td>
                        <span className="hcam-table-status">
                          <CheckCircle2Icon />
                          {item.state}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <section className="hcam-readiness" aria-labelledby="readiness-title">
            <h2 id="readiness-title">
              <FormattedMessage id="workspace.ready" />
            </h2>
            <dl>
              <ReadinessRow label="Contract boundary" value="Bound" />
              <ReadinessRow label="Operational actions" value="Disabled" />
              <ReadinessRow label="Persistent data" value="None" />
              <ReadinessRow label="Locale catalogue" value="Complete" />
            </dl>
          </section>
        </div>
      </main>
      {commandsOpen ? <CommandDialog onClose={() => setCommandsOpen(false)} /> : null}
    </div>
  );
}
function CheckCircle2Icon() {
  return <span className="hcam-status-dot" aria-hidden="true" />;
}
function ReadinessRow({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
function Root({ config }: { readonly config: PortalRuntimeConfig }) {
  const [locale] = useState<Locale>("en");
  return (
    <HcamIntlProvider locale={locale}>
      <BrowserRouter>
        <Shell config={config} />
      </BrowserRouter>
    </HcamIntlProvider>
  );
}
export function createPortalApp(element: HTMLElement, config: PortalRuntimeConfig): () => void {
  const root = createRoot(element);
  root.render(
    <StrictMode>
      <Root config={config} />
    </StrictMode>,
  );
  return () => root.unmount();
}
export function PortalShellPreview({
  config,
  locale = "en",
}: {
  readonly config: PortalRuntimeConfig;
  readonly locale?: Locale;
}): ReactNode {
  return (
    <HcamIntlProvider locale={locale}>
      <BrowserRouter>
        <Shell config={config} />
      </BrowserRouter>
    </HcamIntlProvider>
  );
}
export function ConnectedPortalLink({
  href,
  children,
}: {
  readonly href: `/${string}`;
  readonly children: ReactNode;
}) {
  return (
    <a className="hcam-button hcam-button--default" href={href}>
      {children}
    </a>
  );
}
