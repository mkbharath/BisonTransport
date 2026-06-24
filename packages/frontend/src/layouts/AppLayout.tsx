import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const NAV_ITEMS = [
  { path: "/", label: "Dashboard", icon: "📊" },
  { path: "/orders", label: "Orders", icon: "📦" },
  { path: "/inbox", label: "Inbox", icon: "📧" },
  { path: "/queue", label: "Review Queue", icon: "📋" },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-brand-900 text-white flex flex-col">
        <div className="p-4 border-b border-white/10">
          <h1 className="text-lg font-bold">Order Intelligence</h1>
          <p className="text-xs text-white/60 mt-1">Transportation & Logistics</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path ||
              (item.path !== "/" && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-white/20 text-white font-medium"
                    : "text-white/70 hover:bg-white/10 hover:text-white"
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-white/10">
          <div className="text-sm text-white/80">{user?.name}</div>
          <div className="text-xs text-white/50 capitalize">{user?.role}</div>
          <button
            onClick={logout}
            className="mt-2 text-xs text-white/50 hover:text-white underline"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
