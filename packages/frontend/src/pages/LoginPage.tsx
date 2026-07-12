import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Mail, Lock, ArrowRight } from "lucide-react";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email) {
      setError("Enter your email address first");
      return;
    }
    try {
      await fetch("/api/v1/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setError("");
      alert("If the email exists, a password reset link has been sent.");
    } catch {
      alert("Could not send reset email. Please try again.");
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-[#f0f4f8]">
      {/* Animated gradient blobs */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-gradient-to-br from-teal-300/40 to-cyan-200/30 blur-3xl animate-pulse" />
      <div className="absolute bottom-[-15%] right-[-5%] w-[500px] h-[500px] rounded-full bg-gradient-to-br from-blue-300/30 to-indigo-200/20 blur-3xl animate-pulse" style={{animationDelay: "1s"}} />
      <div className="absolute top-[30%] right-[20%] w-[300px] h-[300px] rounded-full bg-gradient-to-br from-emerald-200/30 to-teal-100/20 blur-2xl animate-pulse" style={{animationDelay: "2s"}} />

      {/* Content */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4">
        {/* Logo */}
        <div className="mb-8">
          <img
            src="/Bison-2022-Logo-RGB_Not-Registered.png"
            alt="Bison Transport"
            className="h-14 object-contain"
          />
        </div>

        {/* Card */}
        <div className="w-full max-w-[420px] bg-white/80 backdrop-blur-xl rounded-3xl p-9 shadow-2xl shadow-gray-300/30 border border-white/60">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Order Intelligence</h1>
            <p className="text-gray-500 text-sm">Sign in to manage your orders</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-[11px] font-bold text-gray-500 mb-2 uppercase tracking-widest">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-teal-400 focus:ring-4 focus:ring-teal-500/10 transition-all shadow-sm"
                  placeholder="you@company.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-gray-500 mb-2 uppercase tracking-widest">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-teal-400 focus:ring-4 focus:ring-teal-500/10 transition-all shadow-sm"
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-100 text-red-600 text-sm px-4 py-3 rounded-xl">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-gradient-to-r from-teal-500 to-cyan-600 text-white rounded-xl font-bold text-sm hover:from-teal-600 hover:to-cyan-700 focus:outline-none focus:ring-4 focus:ring-teal-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-teal-500/20 flex items-center justify-center gap-2"
            >
              {loading ? "Signing in..." : (
                <>Sign In <ArrowRight className="w-4 h-4" /></>
              )}
            </button>

            <div className="text-center">
              <a href="/forgot-password" onClick={(e) => { e.preventDefault(); handleForgotPassword(); }} className="text-sm text-teal-600 hover:text-teal-700 font-medium cursor-pointer">
                Forgot Password?
              </a>
            </div>
          </form>
        </div>

        {/* Powered by */}
        <div className="mt-8 flex items-center gap-2">
          <span className="text-[11px] text-gray-400 font-medium">Powered by</span>
          <img src="/ideyalabs.png" alt="ideyaLabs" className="h-5 object-contain" />
        </div>
      </div>
    </div>
  );
}
