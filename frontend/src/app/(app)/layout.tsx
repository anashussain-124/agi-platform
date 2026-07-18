"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Brain,
  MessageSquare,
  ListChecks,
  Database,
  Settings,
  LogOut,
  Menu,
  X,
  Activity,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: Activity },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/memory", label: "Memory", icon: Database },
  { href: "/tasks", label: "Tasks", icon: ListChecks },
  { href: "/brain", label: "Brain Settings", icon: Brain },
  { href: "/settings", label: "Account", icon: Settings },
];

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem("brain_token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem("brain_token");
    router.push("/login");
  }, [router]);

  if (!mounted) return null;

  // Chat page gets full height without padding
  const isFullHeightRoute = pathname === "/chat";

  return (
    <div className="flex h-full bg-[var(--ink)] bg-grid relative overflow-hidden">
      {/* Background glowing orbs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-[var(--glow-ion)] blur-[120px]" />
        <div className="absolute bottom-[10%] -right-[10%] w-[40%] h-[40%] rounded-full bg-[var(--glow-teal)] blur-[120px]" />
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-50 w-64
          glass border-r border-[var(--hairline)]
          transform transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0
          flex flex-col
        `}
      >
        {/* Logo */}
        <div className="p-6 border-b border-[var(--hairline)]">
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-[var(--gradient-primary)] p-[1px] shadow-[var(--shadow-glow)] transition-transform duration-300 group-hover:scale-105">
              <div className="w-full h-full bg-[var(--ink)] rounded-[11px] flex items-center justify-center">
                <Brain className="w-5 h-5 text-signal brain-glow" />
              </div>
            </div>
            <div>
              <h1 className="text-base font-semibold text-[var(--bone)] tracking-tight font-display">Brain AGI</h1>
              <p className="text-xs text-[var(--muted)] font-mono tracking-widest uppercase">Platform</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
                  ${
                    isActive
                      ? "bg-[var(--ion-dim)] text-[var(--ion)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] border border-[var(--ion-dim)]"
                      : "text-[var(--bone-soft)] hover:text-[var(--bone)] hover:bg-[var(--panel-2)]"
                  }
                `}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-signal" : ""}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-[var(--hairline)]">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-[var(--bone-soft)] hover:text-[#ff6b6b] hover:bg-[rgba(255,107,107,0.1)] w-full transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0 z-10 relative">
        {/* Mobile header */}
        <header className="md:hidden flex items-center gap-3 p-4 glass border-b border-[var(--hairline)] sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-xl hover:bg-[var(--panel-2)] text-[var(--bone-soft)] transition-colors"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[var(--gradient-primary)] p-[1px]">
              <div className="w-full h-full bg-[var(--ink)] rounded-[7px] flex items-center justify-center">
                <Brain className="w-4 h-4 text-signal" />
              </div>
            </div>
            <span className="text-sm font-semibold tracking-tight font-display">Brain AGI</span>
          </div>
        </header>

        {/* Page content */}
        <div className={`flex-1 overflow-y-auto ${isFullHeightRoute ? "p-0" : "p-4 md:p-8"}`}>
          {children}
        </div>
      </main>
    </div>
  );
}
