import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Lock, ArrowRight, CheckCircle } from "lucide-react";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) { setError("Passwords don't match"); return; }
    if (password.length < 8) { setError("Min 8 characters required"); return; }
    if (!/[A-Z]/.test(password)) { setError("Needs an uppercase letter"); return; }
    if (!/[a-z]/.test(password)) { setError("Needs a lowercase letter"); return; }
    if (!/[0-9]/.test(password)) { setError("Needs a number"); return; }

    setLoading(true);
    try {
      const res = await fetch("/api/v1/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data?.detail?.error?.message || "Reset failed");
      }
      setSuccess(true);
      setTimeout(() => navigate("/login"), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-500 font-medium">Invalid reset link. No token provided.</p>
          <a href="/login" className="text-teal-600 text-sm mt-2 inline-block">Back to Login</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f0f4f8] relative overflow-hidden">
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-gradient-to-br from-teal-300/30 to-cyan-200/20 blur-3xl" />
      <div className="absolute bottom-[-15%] right-[-5%] w-[400px] h-[400px] rounded-full bg-gradient-to-br from-blue-300/20 to-indigo-200/10 blur-3xl" />

      <div className="relative z-10 w-full max-w-[420px] px-4">
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-9 shadow-2xl shadow-gray-300/30 border border-white/60">
          {success ? (
            <div className="text-center py-6">
              <CheckCircle className="w-12 h-12 text-teal-500 mx-auto mb-3" />
              <h2 className="text-xl font-bold text-gray-900 mb-1">Password Reset!</h2>
              <p className="text-gray-500 text-sm">Redirecting to login...</p>
            </div>
          ) : (
            <>
              <div className="text-center mb-8">
                <h1 className="text-2xl font-bold text-gray-900 mb-1">Reset Password</h1>
                <p className="text-gray-500 text-sm">Enter your new password</p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-[11px] font-bold text-gray-500 mb-2 uppercase tracking-widest">New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                      className="w-full pl-11 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-teal-400 focus:ring-4 focus:ring-teal-500/10 transition-all shadow-sm"
                      placeholder="Min 8 chars, upper+lower+number" />
                  </div>
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-gray-500 mb-2 uppercase tracking-widest">Confirm Password</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required
                      className={`w-full pl-11 pr-4 py-3.5 bg-white border rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-4 transition-all shadow-sm ${
                        confirm && confirm !== password ? "border-red-300 focus:ring-red-500/10" : "border-gray-200 focus:border-teal-400 focus:ring-teal-500/10"
                      }`}
                      placeholder="Re-enter password" />
                  </div>
                </div>

                {error && <div className="bg-red-50 border border-red-100 text-red-600 text-sm px-4 py-3 rounded-xl">{error}</div>}

                <button type="submit" disabled={loading}
                  className="w-full py-3.5 bg-gradient-to-r from-teal-500 to-cyan-600 text-white rounded-xl font-bold text-sm hover:from-teal-600 hover:to-cyan-700 disabled:opacity-50 transition-all shadow-lg shadow-teal-500/20 flex items-center justify-center gap-2">
                  {loading ? "Resetting..." : (<>Reset Password <ArrowRight className="w-4 h-4" /></>)}
                </button>
              </form>

              <p className="text-center mt-5">
                <a href="/login" className="text-sm text-teal-600 hover:text-teal-700 font-medium">Back to Login</a>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
