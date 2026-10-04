"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  Activity,
  Bell,
  BrainCircuit,
  Building2,
  CornerDownLeft,
  FileText,
  FlaskConical,
  Grid3X3,
  Hospital,
  LogOut,
  MessagesSquare,
  Pill,
  Route,
  Search,
  Settings2,
  ShieldCheck,
  Stethoscope,
  Video,
  Watch,
  type LucideIcon,
} from "lucide-react";

import type { MediLinkUser } from "@/lib/api";
import { notificationSocketUrl } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { initials } from "@/lib/format";
import BrandLogo from "@/components/BrandLogo";
import ThemeToggle from "@/components/ThemeToggle";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  soon?: boolean;
  badge?: string;
};

type Props = {
  user: MediLinkUser;
  logout: () => void;
  nav: NavItem[];
  active: string;
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
};

type ProductLink = {
  h: string;
  l: string;
  i: LucideIcon;
};

type CommandItem = {
  id: string;
  label: string;
  icon: LucideIcon;
  href?: string;
  run: () => void;
};

export default function AppShell({
  user,
  logout,
  nav,
  active,
  title,
  subtitle,
  actions,
  children,
}: Props) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [apps, setApps] = useState(false);
  const [unread, setUnread] = useState(0);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const input = useRef<HTMLInputElement>(null);

  const roleHome =
    user.role === "doctor"
      ? "/dashboard/doctor"
      : user.role === "admin"
        ? "/dashboard/admin"
        : "/dashboard/patient";

  const productLinks = useMemo<ProductLink[]>(() => {
    if (user.role === "patient") {
      return [
        { h: "/copilot", l: "Copilot", i: BrainCircuit },
        { h: "/medications", l: "Medications", i: Pill },
        { h: "/labs", l: "Lab results", i: FlaskConical },
        { h: "/documents", l: "Documents", i: FileText },
        { h: "/referrals", l: "Referrals", i: Route },
        { h: "/hospitals", l: "Hospitals", i: Hospital },
        { h: "/messages", l: "Messages", i: MessagesSquare },
        { h: "/video", l: "Video care", i: Video },
        { h: "/watch", l: "MediLink Watch", i: Watch },
        { h: "/connected-care", l: "Connected care", i: Activity },
        { h: "/settings", l: "Settings", i: Settings2 },
      ];
    }

    if (user.role === "doctor") {
      return [
        { h: "/patients", l: "Patient records", i: FileText },
        { h: "/clinical-actions", l: "Care actions", i: Stethoscope },
        { h: "/messages", l: "Messages", i: MessagesSquare },
        { h: "/video", l: "Video care", i: Video },
        { h: "/watch", l: "Remote monitoring", i: Watch },
        { h: "/connected-care", l: "Connected care", i: Activity },
        { h: "/referrals", l: "Referrals", i: Route },
        { h: "/hospitals", l: "Hospitals", i: Building2 },
        { h: "/settings", l: "Settings", i: Settings2 },
      ];
    }

    return [
      { h: "/dashboard/admin", l: "Operations", i: Building2 },
      { h: "/network", l: "Care network", i: Hospital },
      { h: "/platform", l: "Platform control", i: Settings2 },
      { h: "/intelligence", l: "Model intelligence", i: BrainCircuit },
      { h: "/audit", l: "Audit history", i: FileText },
      { h: "/hospitals", l: "Care network", i: Hospital },
      { h: "/settings", l: "Settings", i: Settings2 },
    ];
  }, [user.role]);

  // Sidebar navigation and the app launcher intentionally overlap. Build one
  // command list by destination so the palette never renders duplicate routes
  // with duplicate React keys (e.g. "Medications").
  const commands = useMemo<CommandItem[]>(() => {
    const routeCommands: CommandItem[] = [
      ...nav
        .filter((n) => !n.soon)
        .map((n) => ({
          id: `route:${n.href}`,
          href: n.href,
          label: n.label,
          icon: n.icon,
          run: () => router.push(n.href),
        })),
      ...productLinks.map((x) => ({
        id: `route:${x.h}`,
        href: x.h,
        label: x.l,
        icon: x.i,
        run: () => router.push(x.h),
      })),
    ];

    const byDestination = new Map<string, CommandItem>();
    for (const command of routeCommands) {
      const destination = command.href ?? command.id;
      if (!byDestination.has(destination)) {
        byDestination.set(destination, command);
      }
    }

    return [
      ...byDestination.values(),
      { id: "action:sign-out", label: "Sign out", icon: LogOut, run: logout },
    ];
  }, [nav, productLinks, router, logout]);

  const results = useMemo(
    () => commands.filter((c) => c.label.toLowerCase().includes(q.toLowerCase())),
    [commands, q],
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((value) => !value);
      }
      if (e.key === "Escape") {
        setOpen(false);
        setApps(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (open) {
      setQ("");
      setSel(0);
      setTimeout(() => input.current?.focus(), 10);
    }
  }, [open]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    const ws = new WebSocket(notificationSocketUrl(token));
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "notification_count") {
          setUnread(Number(message.unread) || 0);
        }
      } catch {
        // Ignore malformed notification frames without disrupting navigation.
      }
    };

    return () => ws.close();
  }, []);

  const run = (index: number) => {
    const command = results[index];
    if (!command) return;
    setOpen(false);
    command.run();
  };

  return (
    <div className="shell">
      <aside className="rail">
        <Link href={roleHome} className="brand">
          <BrandLogo />
        </Link>

        <nav className="railNav">
          {nav.map(({ href, label, icon: Icon, soon, badge }) =>
            soon ? (
              <span key={`soon:${href}`} className="railItem disabled">
                <Icon size={18} />
                {label}
                <em>Soon</em>
              </span>
            ) : (
              <Link
                key={`nav:${href}`}
                href={href}
                className={`railItem${active === href ? " active" : ""}`}
              >
                <Icon size={18} />
                {label}
                {badge && <em className="ai">{badge}</em>}
              </Link>
            ),
          )}
        </nav>

        <div className="railFoot">
          <div className="secureChip">
            <ShieldCheck size={16} />
            <div>
              <b>Protected session</b>
              <small>Role-secured access</small>
            </div>
          </div>
          <div className="whoami">
            <div className={`avatar ${user.role}`}>{initials(user.full_name)}</div>
            <div>
              <b>{user.full_name}</b>
              <small>
                {user.role === "doctor"
                  ? "Clinician"
                  : user.role === "admin"
                    ? "Operations"
                    : "Patient"}
              </small>
            </div>
          </div>
          <button className="logoutAction" onClick={logout}>
            <LogOut size={17} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <div className="shellMain">
        <header className="topbar">
          <button className="paletteTrigger" onClick={() => setOpen(true)}>
            <Search size={16} />
            <span>Search MediLink…</span>
            <kbd>Ctrl K</kbd>
          </button>

          <div className="topTools">
            <div className="appLauncherWrap">
              <button
                className="iconBtn"
                onClick={() => setApps((value) => !value)}
                aria-label="MediLink apps"
              >
                <Grid3X3 size={18} />
              </button>
              {apps && (
                <div className="appLauncher">
                  {productLinks.map(({ h, l, i: Icon }) => (
                    <Link
                      href={h}
                      key={`app:${h}`}
                      onClick={() => setApps(false)}
                    >
                      <Icon size={19} />
                      <span>{l}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <ThemeToggle />
            <Link className="iconBtn" href="/notifications" aria-label="Notifications">
              <Bell size={18} />
              {unread > 0 && <i className="dot" />}
              {unread > 0 && (
                <span className="notifCount">{unread > 9 ? "9+" : unread}</span>
              )}
            </Link>
            <div className={`avatar ${user.role}`}>{initials(user.full_name)}</div>
          </div>
        </header>

        <div className="shellBody">
          <div className="pageHead">
            <div>
              <h1>{title}</h1>
              {subtitle && <p>{subtitle}</p>}
            </div>
            {actions && <div className="pageActions">{actions}</div>}
          </div>
          {children}
        </div>
      </div>

      <nav className="tabbar">
        {nav
          .filter((n) => !n.soon)
          .slice(0, 5)
          .map(({ href, label, icon: Icon }) => (
            <Link
              key={`tab:${href}`}
              href={href}
              className={active === href ? "active" : ""}
            >
              <Icon size={20} />
              <span>{label.split(" ")[0]}</span>
            </Link>
          ))}
      </nav>

      {open && (
        <div className="paletteBackdrop" onMouseDown={() => setOpen(false)}>
          <div className="palette" onMouseDown={(e) => e.stopPropagation()}>
            <div className="paletteInput">
              <Search size={18} />
              <input
                ref={input}
                value={q}
                placeholder="Where do you want to go?"
                onChange={(e) => {
                  setQ(e.target.value);
                  setSel(0);
                }}
                onKeyDown={(e) => {
                  if (e.key === "ArrowDown") {
                    e.preventDefault();
                    setSel((s) => Math.min(s + 1, results.length - 1));
                  }
                  if (e.key === "ArrowUp") {
                    e.preventDefault();
                    setSel((s) => Math.max(s - 1, 0));
                  }
                  if (e.key === "Enter") run(sel);
                }}
              />
            </div>

            <ul>
              {results.length === 0 && (
                <li className="paletteEmpty">Nothing matches “{q}”.</li>
              )}
              {results.map((command, index) => (
                <li key={command.id}>
                  <button
                    className={index === sel ? "on" : ""}
                    onMouseEnter={() => setSel(index)}
                    onClick={() => run(index)}
                  >
                    <command.icon size={17} />
                    {command.label}
                    {index === sel && <CornerDownLeft size={14} />}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
