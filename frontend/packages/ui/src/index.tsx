import {
  Activity,
  AlertCircle,
  ArrowRight,
  BellRing,
  BrainCircuit,
  Camera,
  CheckCircle2,
  ChevronDown,
  CircleDashed,
  Command,
  FileCheck2,
  FileSearch,
  FolderClock,
  Gauge,
  Info,
  KeyRound,
  LayoutDashboard,
  Map,
  PanelsTopLeft,
  RadioTower,
  RefreshCw,
  Search,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  TriangleAlert,
  UsersRound,
  Video,
  X,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import {
  Children,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type ReactNode,
} from "react";
import type { UiState } from "@hcam/contracts";

export function IconButton({
  label,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  readonly label: string;
  readonly children: ReactNode;
}) {
  return (
    <button className="hcam-icon-button" type="button" aria-label={label} title={label} {...props}>
      {children}
    </button>
  );
}
export function Button({
  children,
  variant = "default",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  readonly variant?: "default" | "primary" | "danger";
}) {
  return (
    <button className={`hcam-button hcam-button--${variant}`} type="button" {...props}>
      {children}
    </button>
  );
}
export function VisuallyHidden({ children }: { readonly children: ReactNode }) {
  return <span className="hcam-visually-hidden">{children}</span>;
}

export type HcamPortalId =
  | "command"
  | "gis"
  | "operations"
  | "intelligence"
  | "investigations"
  | "evidence"
  | "admin"
  | "security";

interface PortalDestination {
  readonly id: HcamPortalId;
  readonly label: string;
  readonly description: string;
  readonly path: `/${string}`;
  readonly localPort: number;
  readonly icon: LucideIcon;
}

const portalGroups: readonly {
  readonly label: string;
  readonly portals: readonly PortalDestination[];
}[] = [
  {
    label: "Operations",
    portals: [
      {
        id: "command",
        label: "Command Center",
        description: "Situation and coordination",
        path: "/command",
        localPort: 4173,
        icon: ShieldCheck,
      },
      {
        id: "gis",
        label: "GIS Center",
        description: "Spatial operations",
        path: "/gis",
        localPort: 4174,
        icon: Map,
      },
      {
        id: "operations",
        label: "Operations Center",
        description: "Cameras and platform health",
        path: "/operations",
        localPort: 4180,
        icon: RadioTower,
      },
    ],
  },
  {
    label: "Intelligence",
    portals: [
      {
        id: "intelligence",
        label: "Intelligence Center",
        description: "Analysis and human review",
        path: "/intelligence",
        localPort: 4175,
        icon: BrainCircuit,
      },
      {
        id: "investigations",
        label: "Investigation Center",
        description: "Chronology and reconstruction",
        path: "/investigations",
        localPort: 4176,
        icon: FolderClock,
      },
      {
        id: "evidence",
        label: "Evidence Desk",
        description: "Integrity and provenance",
        path: "/evidence",
        localPort: 4177,
        icon: FileCheck2,
      },
    ],
  },
  {
    label: "Governance",
    portals: [
      {
        id: "admin",
        label: "Admin Center",
        description: "Policy and configuration",
        path: "/admin",
        localPort: 4178,
        icon: Settings2,
      },
      {
        id: "security",
        label: "Security Center",
        description: "Assurance and audit",
        path: "/security",
        localPort: 4179,
        icon: ShieldAlert,
      },
    ],
  },
] as const;

function portalHref(portal: PortalDestination): string {
  if (
    typeof window !== "undefined" &&
    (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost")
  ) {
    return `${window.location.protocol}//${window.location.hostname}:${portal.localPort}${portal.path}`;
  }
  return portal.path;
}

export function PortalSwitcher({ current }: { readonly current: HcamPortalId }) {
  const switcherRef = useRef<HTMLDetailsElement>(null);
  const currentPortal = portalGroups
    .flatMap((group) => group.portals)
    .find((portal) => portal.id === current);
  const CurrentIcon = currentPortal?.icon ?? PanelsTopLeft;
  useEffect(() => {
    const closeSwitcher = (event: KeyboardEvent | PointerEvent) => {
      const switcher = switcherRef.current;
      if (!switcher) return;
      if (event instanceof KeyboardEvent && event.altKey && event.key.toLowerCase() === "w") {
        event.preventDefault();
        switcher.open = true;
        switcher.querySelector<HTMLElement>("a[aria-current='page'], a")?.focus();
        return;
      }
      if (!switcher.open) return;
      if (event instanceof KeyboardEvent && event.key === "Escape") {
        switcher.open = false;
        switcher.querySelector<HTMLElement>("summary")?.focus();
      }
      if (event instanceof PointerEvent && !switcher.contains(event.target as Node)) {
        switcher.open = false;
      }
    };
    document.addEventListener("keydown", closeSwitcher);
    document.addEventListener("pointerdown", closeSwitcher);
    return () => {
      document.removeEventListener("keydown", closeSwitcher);
      document.removeEventListener("pointerdown", closeSwitcher);
    };
  }, []);
  return (
    <details ref={switcherRef} className="hcam-portal-switcher">
      <summary
        aria-label={`Switch workspace. Current workspace: ${currentPortal?.label ?? current}`}
        aria-keyshortcuts="Alt+W"
      >
        <CurrentIcon size={17} aria-hidden="true" />
        <span>
          <small>Workspace</small>
          <strong>{currentPortal?.label ?? current}</strong>
        </span>
        <ChevronDown className="hcam-portal-switcher__chevron" size={15} aria-hidden="true" />
      </summary>
      <div className="hcam-portal-menu">
        <header>
          <div>
            <strong>Switch workspace</strong>
            <span>One platform, purpose-built centers</span>
          </div>
          <span aria-label="Keyboard shortcuts: Alt W to open, Escape to close">
            <kbd>Alt W</kbd> <kbd>Esc</kbd>
          </span>
        </header>
        {portalGroups.map((group) => (
          <section key={group.label} aria-label={group.label}>
            <h2>{group.label}</h2>
            <div>
              {group.portals.map((portal) => {
                const PortalIcon = portal.icon;
                return (
                  <a
                    key={portal.id}
                    href={portalHref(portal)}
                    aria-current={portal.id === current ? "page" : undefined}
                    onClick={() => {
                      if (switcherRef.current) switcherRef.current.open = false;
                    }}
                  >
                    <PortalIcon size={18} aria-hidden="true" />
                    <span>
                      <strong>{portal.label}</strong>
                      <small>{portal.description}</small>
                    </span>
                    <ArrowRight size={15} aria-hidden="true" />
                  </a>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </details>
  );
}

export function NavigationSection({
  label,
  children,
}: {
  readonly label: string;
  readonly children: ReactNode;
}) {
  const labelId = useId();
  const routeCount = Children.count(children);
  return (
    <details className="hcam-nav-section" role="group" aria-labelledby={labelId} open>
      <summary id={labelId}>
        <span>{label}</span>
        <small aria-hidden="true">{routeCount}</small>
      </summary>
      <div>{children}</div>
    </details>
  );
}

const routeGlyphRules: readonly [RegExp, LucideIcon][] = [
  [/\/live|\/wall/, Video],
  [/camera/, Camera],
  [/map|spatial|coverage|geograph|movement/, Map],
  [/review|alert/, BellRing],
  [/investigation|timeline|reconstruction|comparison|correction/, FileSearch],
  [/evidence|integrity|provenance|custody/, FileCheck2],
  [/user|identit|role|organization|session|access|membership/, UsersRound],
  [/security|denial|privileged|audit|compliance|supply|soc/, ShieldAlert],
  [/profile|configuration|provider|retention|change|policy|feature/, Settings2],
  [/health|service|queue|data|runtime|slo|degradation|recovery|capacity|topology/, Activity],
  [/workload|workspace|briefing/, PanelsTopLeft],
  [/rule|hypoth|relationship|correlation|intelligence/, BrainCircuit],
  [/permission|secret|key/, KeyRound],
  [/metric|budget/, Gauge],
];

export function RouteGlyph({ path }: { readonly path: string }) {
  const match = routeGlyphRules.find(([pattern]) => pattern.test(path));
  const Glyph = match?.[1] ?? LayoutDashboard;
  return <Glyph className="hcam-route-glyph" size={16} strokeWidth={1.9} aria-hidden="true" />;
}

export interface WorkspaceSearchItem {
  readonly label: string;
  readonly href: string;
  readonly group: string;
  readonly keywords?: readonly string[];
}

export function WorkspaceCommandPalette({
  title,
  placeholder,
  boundary,
  items,
  onClose,
}: {
  readonly title: string;
  readonly placeholder: string;
  readonly boundary: string;
  readonly items: readonly WorkspaceSearchItem[];
  readonly onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLElement>(null);
  const boundaryId = useId();
  const resultsId = useId();
  const statusId = useId();
  const searchableItems = useMemo(() => {
    const currentPortal = portalGroups
      .flatMap((group) => group.portals)
      .find((portal) =>
        items.some((item) => item.href === portal.path || item.href.startsWith(`${portal.path}/`)),
      );
    const workspaceItems = portalGroups
      .flatMap((group) => group.portals)
      .filter((portal) => portal.id !== currentPortal?.id)
      .map((portal) => ({
        label: portal.label,
        href: portalHref(portal),
        group: "Platform workspaces",
        keywords: [portal.description, portal.id],
      }));
    return [...items, ...workspaceItems];
  }, [items]);
  const filteredItems = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase();
    if (!needle) return searchableItems;
    return searchableItems.filter((item) =>
      [item.label, item.group, ...(item.keywords ?? [])]
        .join(" ")
        .toLocaleLowerCase()
        .includes(needle),
    );
  }, [query, searchableItems]);
  const groupedItems = useMemo(
    () =>
      [...new Set(filteredItems.map((item) => item.group))].map((group) => ({
        group,
        items: filteredItems.filter((item) => item.group === group),
      })),
    [filteredItems],
  );
  const resultLinks = () =>
    Array.from(resultsRef.current?.querySelectorAll<HTMLAnchorElement>("a") ?? []);
  const focusResult = (index: number) => {
    const links = resultLinks();
    if (links.length) links[Math.max(0, Math.min(index, links.length - 1))]?.focus();
  };
  const handleResultKeyDown = (event: React.KeyboardEvent<HTMLAnchorElement>) => {
    const links = resultLinks();
    const index = links.indexOf(event.currentTarget);
    if (event.key === "ArrowDown") {
      event.preventDefault();
      focusResult(index === links.length - 1 ? 0 : index + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      if (index <= 0) inputRef.current?.focus();
      else focusResult(index - 1);
    } else if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      focusResult(event.key === "Home" ? 0 : links.length - 1);
    }
  };

  return (
    <ModalDialog title={title} onClose={onClose}>
      <div className="hcam-route-palette">
        <header>
          <div>
            <Command size={18} aria-hidden="true" />
            <div>
              <h2>{title}</h2>
              <p id={boundaryId}>{boundary}</p>
            </div>
          </div>
          <div>
            <kbd>Esc</kbd>
            <IconButton label="Close workspace search" onClick={onClose}>
              <X size={17} aria-hidden="true" />
            </IconButton>
          </div>
        </header>
        <label className="hcam-route-palette__search">
          <Search size={18} aria-hidden="true" />
          <input
            ref={inputRef}
            data-initial-focus
            type="search"
            aria-label="Filter available routes"
            aria-controls={resultsId}
            aria-describedby={`${boundaryId} ${statusId}`}
            aria-keyshortcuts="Control+K Meta+K"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                focusResult(0);
              } else if (event.key === "ArrowUp") {
                event.preventDefault();
                focusResult(resultLinks().length - 1);
              }
            }}
            placeholder={placeholder}
            autoComplete="off"
          />
          <span id={statusId} role="status" aria-live="polite" aria-atomic="true">
            {filteredItems.length} destinations
          </span>
        </label>
        <nav
          ref={resultsRef}
          id={resultsId}
          className="hcam-route-palette__results"
          aria-label="Navigation search results"
        >
          {groupedItems.length ? (
            groupedItems.map((group) => (
              <section key={group.group} aria-label={group.group}>
                <h3>{group.group}</h3>
                <div>
                  {group.items.map((item) => (
                    <a
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      onKeyDown={handleResultKeyDown}
                    >
                      <RouteGlyph path={item.href} />
                      <span>{item.label}</span>
                      <ArrowRight size={15} aria-hidden="true" />
                    </a>
                  ))}
                </div>
              </section>
            ))
          ) : (
            <div className="hcam-route-palette__empty">
              <Search size={22} aria-hidden="true" />
              <strong>No matching views</strong>
              <span>Try a route, workflow, or workspace name.</span>
            </div>
          )}
        </nav>
      </div>
    </ModalDialog>
  );
}

const stateIcons: Record<UiState, LucideIcon> = {
  loading: CircleDashed,
  empty: Info,
  ready: CheckCircle2,
  partial: AlertCircle,
  stale: TriangleAlert,
  degraded: ShieldAlert,
  denied: ShieldAlert,
  conflict: AlertCircle,
  failure: XCircle,
  recovery: RefreshCw,
  correction: Info,
  unknown: CircleDashed,
  retracted: XCircle,
  unsupported: ShieldAlert,
  success: CheckCircle2,
};
export function StateBanner({
  state,
  title,
  detail,
  action,
}: {
  readonly state: UiState;
  readonly title: string;
  readonly detail?: string;
  readonly action?: ReactNode;
}) {
  const Icon = stateIcons[state];
  return (
    <section
      className={`hcam-state hcam-state--${state}`}
      aria-live={state === "ready" ? "polite" : "assertive"}
      aria-busy={state === "loading" || state === "recovery"}
    >
      <Icon aria-hidden="true" size={20} />
      <div>
        <strong>{title}</strong>
        {detail ? <p>{detail}</p> : null}
      </div>
      {action ? <div className="hcam-state__action">{action}</div> : null}
    </section>
  );
}
export function Metric({
  label,
  value,
  status = "neutral",
}: {
  readonly label: string;
  readonly value: string;
  readonly status?: "neutral" | "good" | "warning";
}) {
  return (
    <div className={`hcam-metric hcam-metric--${status}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function ModalDialog({
  title,
  onClose,
  children,
}: {
  readonly title: string;
  readonly onClose: () => void;
  readonly children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return undefined;
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    dialog.showModal();
    const focusTarget =
      dialog.querySelector<HTMLElement>("[data-initial-focus]") ??
      dialog.querySelector<HTMLElement>(
        "input:not([disabled]), button:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])",
      );
    focusTarget?.focus();
    const handleClose = () => onClose();
    dialog.addEventListener("cancel", handleClose);
    return () => {
      dialog.removeEventListener("cancel", handleClose);
      if (dialog.open) dialog.close();
      returnFocusRef.current?.focus();
    };
  }, [onClose]);
  return (
    <dialog
      ref={ref}
      className="hcam-native-dialog"
      aria-label={title}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="hcam-command-dialog">{children}</div>
    </dialog>
  );
}
export function TextField({
  label,
  error,
  ...props
}: Omit<React.InputHTMLAttributes<HTMLInputElement>, "aria-invalid"> & {
  readonly label: string;
  readonly error?: string;
}) {
  const inputId = useId();
  const errorId = useId();
  return (
    <div className="hcam-field">
      <label htmlFor={inputId}>{label}</label>
      <input
        id={inputId}
        {...props}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
      />
      {error ? (
        <small id={errorId} role="alert">
          {error}
        </small>
      ) : null}
    </div>
  );
}
export function SelectField({
  label,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & {
  readonly label: string;
  readonly children: ReactNode;
}) {
  return (
    <label className="hcam-field">
      <span>{label}</span>
      <select {...props}>{children}</select>
    </label>
  );
}
export function Disclosure({
  summary,
  children,
}: {
  readonly summary: string;
  readonly children: ReactNode;
}) {
  return (
    <details className="hcam-disclosure">
      <summary>{summary}</summary>
      <div>{children}</div>
    </details>
  );
}
export function TruthBoundary({
  title,
  children,
}: {
  readonly title: string;
  readonly children: ReactNode;
}) {
  return (
    <aside className="hcam-state hcam-state--partial" role="note">
      <ShieldAlert aria-hidden="true" size={20} />
      <div>
        <strong>{title}</strong>
        <p>{children}</p>
      </div>
    </aside>
  );
}

export function QualifiedProjectionBadge({ children }: { readonly children: ReactNode }) {
  return (
    <span className="hcam-state hcam-state--partial" role="status">
      <ShieldAlert aria-hidden="true" size={16} />
      {children}
    </span>
  );
}
export function NonEffectiveButton({ children }: { readonly children: ReactNode }) {
  return (
    <Button disabled aria-disabled="true">
      {children}
    </Button>
  );
}
