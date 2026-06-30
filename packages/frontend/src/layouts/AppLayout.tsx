import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import {
  LayoutDashboard,
  Package,
  Mail,
  ClipboardCheck,
  Settings,
  FileText,
  LogOut,
  ChevronRight,
} from "lucide-react";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard, minRole: "readonly" as const },
  { path: "/orders", label: "Orders", icon: Package, minRole: "readonly" as const },
  { path: "/inbox", label: "Inbox", icon: Mail, minRole: "agent" as const },
  { path: "/queue", label: "Review Queue", icon: ClipboardCheck, minRole: "agent" as const },
  { path: "/audit", label: "Audit Logs", icon: FileText, minRole: "supervisor" as const },
  { path: "/admin", label: "Administration", icon: Settings, minRole: "admin" as const },
];

const ROLE_LEVEL: Record<string, number> = {
  readonly: 0,
  agent: 1,
  supervisor: 2,
  admin: 3,
};

function hasAccess(userRole: string | undefined, minRole: string): boolean {
  const userLevel = ROLE_LEVEL[userRole || "readonly"] ?? 0;
  const requiredLevel = ROLE_LEVEL[minRole] ?? 0;
  return userLevel >= requiredLevel;
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside className="w-[260px] flex-shrink-0 bg-[#0f1b2d] text-white flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/5">
          <img
            src="/Bison-2022-Logo-RGB_Not-Registered.png"
            alt="Bison Transport"
            className="h-9 object-contain brightness-0 invert"
          />
          <p className="text-[11px] text-slate-300 mt-1.5 tracking-wide uppercase">
            Order Intelligence Platform
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-5 space-y-0.5">
          <p className="px-3 mb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
            Menu
          </p>
          {NAV_ITEMS.filter((item) => hasAccess(user?.role, item.minRole)).map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.path ||
              (item.path !== "/" && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-[14px] font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-gradient-to-r from-amber-500/20 to-orange-500/10 text-amber-400 border border-amber-500/20"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? "text-amber-400" : "text-slate-500"}`} />
                <span className="flex-1">{item.label}</span>
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-amber-400/60" />}
              </Link>
            );
          })}
        </nav>

        {/* User + Powered By */}
        <div className="px-3 py-4 border-t border-white/5">
          <div className="flex items-center gap-3 px-2 mb-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-[11px] font-bold text-white shadow-lg shadow-amber-500/20">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-medium text-slate-200 truncate">{user?.name}</p>
              <p className="text-[11px] text-slate-500 capitalize">{user?.role}</p>
            </div>
            <button
              onClick={logout}
              className="p-1.5 rounded-md text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
          {/* Powered by */}
          <div className="flex items-center gap-2 px-2">
            <span className="text-[11px] text-slate-300 uppercase tracking-wider">Powered by</span>
            <img src="/ideyalabs.png" alt="ideyaLabs" className="h-6 object-contain opacity-90" />
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50">
          <div className="animate-fade-in max-w-[1400px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
