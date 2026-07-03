import { Link, Outlet, useLocation } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { changePassword } from "../lib/api";
import {
  LayoutDashboard,
  Package,
  Mail,
  ClipboardCheck,
  Settings,
  FileText,
  LogOut,
  ChevronRight,
  Key,
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
  const [showPasswordModal, setShowPasswordModal] = useState(false);

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
              onClick={() => setShowPasswordModal(true)}
              className="p-1.5 rounded-md text-slate-500 hover:text-amber-400 hover:bg-amber-500/10 transition-colors"
              title="Change Password"
            >
              <Key className="w-3.5 h-3.5" />
            </button>
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

      {/* Change Password Modal */}
      {showPasswordModal && (
        <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
    </div>
  );
}


function ChangePasswordModal({ onClose }: { onClose: () => void }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match");
      return;
    }
    if (newPassword.length < 6) {
      setError("Password must be at least 8 characters with at least one uppercase, one lowercase, and one number");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (!/[A-Z]/.test(newPassword)) {
      setError("Password must contain at least one uppercase letter");
      return;
    }
    if (!/[a-z]/.test(newPassword)) {
      setError("Password must contain at least one lowercase letter");
      return;
    }
    if (!/[0-9]/.test(newPassword)) {
      setError("Password must contain at least one number");
      return;
    }
    setLoading(true);
    try {
      await changePassword(currentPassword, newPassword);
      setSuccess(true);
      setTimeout(onClose, 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to change password";
      setError(msg.includes("incorrect") ? "Current password is incorrect" : msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl p-6 w-[400px] shadow-2xl">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Change Password</h3>
        {success ? (
          <div className="text-center py-4">
            <p className="text-emerald-600 font-medium">Password changed successfully!</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Current Password</label>
              <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">New Password</label>
              <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Confirm New Password</label>
              <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800">Cancel</button>
              <button type="submit" disabled={loading} className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 disabled:opacity-50">
                {loading ? "Changing..." : "Change Password"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
