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
  Menu,
  X,
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
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  // Close sidebar on navigation (mobile)
  const handleNavClick = () => setSidebarOpen(false);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-[270px] bg-white shadow-xl flex flex-col transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0 lg:flex-shrink-0 lg:shadow-none lg:border-r lg:border-gray-100 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        {/* Logo */}
        <div className="px-6 pt-6 pb-4 flex items-center justify-between">
          <div>
            <img
              src="/Bison-2022-Logo-RGB_Not-Registered.png"
              alt="Bison Transport"
              className="h-10 object-contain"
            />
            <p className="text-[10px] text-gray-400 mt-2 tracking-widest uppercase font-semibold">
              Order Intelligence
            </p>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.filter((item) => hasAccess(user?.role, item.minRole)).map((item) => {
            const Icon = item.icon;
            const isActive =
              location.pathname === item.path ||
              (item.path !== "/" && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={handleNavClick}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-[13px] font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-gradient-to-r from-teal-500 to-cyan-500 text-white shadow-lg shadow-teal-500/25"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                }`}
              >
                <Icon className={`w-[18px] h-[18px] ${isActive ? "text-white" : "text-gray-400"}`} />
                <span className="flex-1">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User + Powered By */}
        <div className="px-4 py-4 border-t border-gray-100">
          <div className="flex items-center gap-3 px-2 mb-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center text-[11px] font-bold text-white shadow-md shadow-teal-400/20">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-semibold text-gray-800 truncate">{user?.name}</p>
              <p className="text-[11px] text-gray-400 capitalize">{user?.role}</p>
            </div>
            <button
              onClick={() => setShowPasswordModal(true)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-teal-600 hover:bg-teal-50 transition-colors"
              title="Change Password"
            >
              <Key className="w-4 h-4" />
            </button>
            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center gap-2 px-2">
            <span className="text-[9px] text-gray-400 uppercase tracking-widest">Powered by</span>
            <img src="/ideyalabs.png" alt="ideyaLabs" className="h-5 object-contain" />
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Top Bar */}
        <div className="lg:hidden flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-100 shadow-sm">
          <button onClick={() => setSidebarOpen(true)} className="p-1.5 text-gray-600 hover:text-gray-900">
            <Menu className="w-5 h-5" />
          </button>
          <img
            src="/Bison-2022-Logo-RGB_Not-Registered.png"
            alt="Bison Transport"
            className="h-7 object-contain"
          />
        </div>
        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-50">
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
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const passwordStrength = (() => {
    if (!newPassword) return { score: 0, label: "", color: "" };
    let score = 0;
    if (newPassword.length >= 8) score++;
    if (/[A-Z]/.test(newPassword)) score++;
    if (/[a-z]/.test(newPassword)) score++;
    if (/[0-9]/.test(newPassword)) score++;
    if (/[^A-Za-z0-9]/.test(newPassword)) score++;
    if (score <= 2) return { score, label: "Weak", color: "bg-red-500" };
    if (score <= 3) return { score, label: "Fair", color: "bg-amber-500" };
    if (score <= 4) return { score, label: "Good", color: "bg-blue-500" };
    return { score, label: "Strong", color: "bg-emerald-500" };
  })();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match");
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
      setTimeout(onClose, 2000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to change password";
      setError(msg.includes("incorrect") ? "Current password is incorrect" : msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl w-[440px] shadow-2xl shadow-gray-300/30 border border-gray-100 overflow-hidden">
        {/* Header */}
        <div className="px-7 pt-7 pb-4">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <Key className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Change Password</h3>
              <p className="text-xs text-gray-400">Update your account security</p>
            </div>
          </div>
        </div>

        {success ? (
          <div className="px-7 pb-7 text-center py-8">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-teal-50 flex items-center justify-center">
              <svg className="w-7 h-7 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            </div>
            <p className="text-teal-600 font-semibold text-sm">Password changed successfully!</p>
            <p className="text-gray-400 text-xs mt-1">Redirecting...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-7 pb-7">
            {/* Current Password */}
            <div className="mb-4">
              <label className="block text-[11px] font-bold text-gray-500 mb-1.5 uppercase tracking-widest">Current Password</label>
              <div className="relative">
                <input
                  type={showCurrent ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-teal-400 focus:ring-4 focus:ring-teal-500/10 focus:bg-white transition-all pr-10"
                  placeholder="Enter current password"
                />
                <button type="button" onClick={() => setShowCurrent(!showCurrent)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={showCurrent ? "M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" : "M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178zM15 12a3 3 0 11-6 0 3 3 0 016 0z"} /></svg>
                </button>
              </div>
            </div>

            {/* Divider */}
            <div className="border-t border-gray-100 my-5" />

            {/* New Password */}
            <div className="mb-4">
              <label className="block text-[11px] font-bold text-gray-500 mb-1.5 uppercase tracking-widest">New Password</label>
              <div className="relative">
                <input
                  type={showNew ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-teal-400 focus:ring-4 focus:ring-teal-500/10 focus:bg-white transition-all pr-10"
                  placeholder="Min 8 characters"
                />
                <button type="button" onClick={() => setShowNew(!showNew)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={showNew ? "M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" : "M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178zM15 12a3 3 0 11-6 0 3 3 0 016 0z"} /></svg>
                </button>
              </div>
              {/* Strength meter */}
              {newPassword && (
                <div className="mt-2">
                  <div className="flex gap-1 mb-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className={`h-1.5 flex-1 rounded-full transition-all ${i <= passwordStrength.score ? passwordStrength.color : "bg-gray-100"}`} />
                    ))}
                  </div>
                  <p className={`text-[10px] font-semibold ${passwordStrength.score <= 2 ? "text-red-500" : passwordStrength.score <= 3 ? "text-amber-500" : "text-teal-500"}`}>
                    {passwordStrength.label}
                  </p>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div className="mb-4">
              <label className="block text-[11px] font-bold text-gray-500 mb-1.5 uppercase tracking-widest">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className={`w-full px-4 py-3 bg-gray-50 border rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-4 transition-all ${
                  confirmPassword && confirmPassword !== newPassword
                    ? "border-red-300 focus:border-red-400 focus:ring-red-500/10"
                    : confirmPassword && confirmPassword === newPassword
                    ? "border-teal-300 focus:border-teal-400 focus:ring-teal-500/10"
                    : "border-gray-200 focus:border-teal-400 focus:ring-teal-500/10"
                }`}
                placeholder="Re-enter new password"
              />
              {confirmPassword && confirmPassword !== newPassword && (
                <p className="text-[10px] text-red-500 mt-1 font-medium">Passwords don't match</p>
              )}
              {confirmPassword && confirmPassword === newPassword && (
                <p className="text-[10px] text-teal-500 mt-1 font-medium">Passwords match</p>
              )}
            </div>

            {/* Requirements */}
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-3 mb-5">
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-2">Requirements</p>
              <div className="grid grid-cols-2 gap-1.5">
                {[
                  { met: newPassword.length >= 8, text: "8+ characters" },
                  { met: /[A-Z]/.test(newPassword), text: "Uppercase letter" },
                  { met: /[a-z]/.test(newPassword), text: "Lowercase letter" },
                  { met: /[0-9]/.test(newPassword), text: "Number" },
                ].map(({ met, text }) => (
                  <div key={text} className="flex items-center gap-1.5">
                    <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${met ? "bg-teal-100" : "bg-gray-100"}`}>
                      {met && <svg className="w-2 h-2 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                    </div>
                    <span className={`text-[11px] font-medium ${met ? "text-teal-600" : "text-gray-400"}`}>{text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-100 text-red-600 text-xs px-3 py-2.5 rounded-xl mb-4 font-medium">
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3">
              <button type="button" onClick={onClose} className="px-4 py-2.5 text-sm font-medium text-gray-500 hover:text-gray-700 rounded-xl hover:bg-gray-50 transition-all">
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || passwordStrength.score < 4}
                className="px-5 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-teal-500 to-cyan-600 rounded-xl hover:from-teal-600 hover:to-cyan-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-teal-500/20"
              >
                {loading ? "Updating..." : "Update Password"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
