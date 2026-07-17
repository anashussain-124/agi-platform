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
      // First try to login
      try {
        const data = await api.login(email, password);
        localStorage.setItem("brain_token", data.token);
        showToast("Welcome back!", "success");
        router.push("/dashboard");
        return;
      } catch (err: any) {
        // If they don't exist (Unauthorized or Invalid credentials), try to register them automatically for convenience
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
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center items-center relative overflow-hidden bg-grid">
      {/* Background glowing orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-[var(--glow-violet)] blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-[var(--glow-teal)] blur-[120px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md p-6 sm:p-8 relative z-10"
      >
        <div className="glass-strong p-8 rounded-3xl shadow-2xl card-hover border border-zinc-800/50">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-[var(--gradient-primary)] p-[1px] mb-6 shadow-[var(--shadow-glow)]">
              <div className="w-full h-full bg-zinc-950 rounded-[15px] flex items-center justify-center">
                <Brain className="w-8 h-8 text-violet-400 brain-glow" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight text-center">AGI Platform</h1>
            <p className="text-zinc-400 text-sm mt-2 text-center">Login or register to access your Brain</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-4">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className="w-5 h-5 text-zinc-500 group-focus-within:text-violet-400 transition-colors" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email Address"
                  className="w-full bg-zinc-900/50 border border-zinc-800/80 text-white rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-1 focus:ring-violet-500 focus:border-violet-500 transition-all placeholder:text-zinc-600 glass"
                  required
                  disabled={loading}
                />
              </div>

              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="w-5 h-5 text-zinc-500 group-focus-within:text-violet-400 transition-colors" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full bg-zinc-900/50 border border-zinc-800/80 text-white rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-1 focus:ring-violet-500 focus:border-violet-500 transition-all placeholder:text-zinc-600 glass"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[var(--gradient-primary)] hover:opacity-90 text-zinc-950 font-semibold py-3 px-4 rounded-xl transition-all flex items-center justify-center gap-2 shadow-[var(--shadow-glow)] disabled:opacity-70 disabled:cursor-not-allowed group mt-2"
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

        <p className="text-center text-zinc-600 font-medium text-xs mt-8">
          Secured by AGI Core
        </p>
      </motion.div>
    </div>
  );
}
