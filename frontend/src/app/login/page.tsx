"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Brain, Lock, User, ArrowRight, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { showToast } from "@/components/ui/toast";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setLoading(true);

    try {
      try {
        const data = await api.login(email, password);
        localStorage.setItem("brain_token", data.token);
        showToast("Welcome back!", "success");
        router.push("/dashboard");
        return;
      } catch (err: any) {
        if (err.message.toLowerCase().includes("invalid") || err.message.toLowerCase().includes("unauthorized") || err.message.includes("401")) {
          const data = await api.register(email, password, email.split("@")[0]);
          localStorage.setItem("brain_token", data.token);
          showToast("Account created successfully!", "success");
          router.push("/dashboard");
          return;
        }
        throw err;
      }
    } catch (err: any) {
      showToast(err.message || "Authentication failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--ink)] flex flex-col justify-center items-center relative overflow-hidden bg-grid">
      {/* Background glowing orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-[var(--glow-ion)] blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-[var(--glow-teal)] blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md p-6 sm:p-8 relative z-10"
      >
        <div className="instrument ticks p-8 rounded-3xl shadow-2xl border border-[var(--hairline-strong)]">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-[var(--gradient-primary)] p-[1px] mb-6 shadow-[var(--shadow-glow)]">
              <div className="w-full h-full bg-[var(--ink)] rounded-[15px] flex items-center justify-center">
                <Brain className="w-8 h-8 text-signal brain-glow" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-[var(--bone)] tracking-tight text-center font-display">AGI Platform</h1>
            <p className="text-[var(--muted)] text-sm mt-2 text-center">Login or register to access your Brain</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-4">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className="w-5 h-5 text-[var(--muted)] group-focus-within:text-signal transition-colors" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email Address"
                  className="w-full bg-[var(--panel-2)] border border-[var(--hairline-strong)] text-[var(--bone)] rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-1 focus:ring-signal focus:border-signal transition-all placeholder:text-[var(--muted)]"
                  required
                  disabled={loading}
                />
              </div>

              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="w-5 h-5 text-[var(--muted)] group-focus-within:text-signal transition-colors" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full bg-[var(--panel-2)] border border-[var(--hairline-strong)] text-[var(--bone)] rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-1 focus:ring-signal focus:border-signal transition-all placeholder:text-[var(--muted)]"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary justify-center disabled:opacity-70 disabled:cursor-not-allowed group mt-2"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  Continue
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-[var(--muted)] font-medium text-xs mt-8 font-mono tracking-wide">
          SECURED BY AGI CORE
        </p>
      </motion.div>
    </div>
  );
}
