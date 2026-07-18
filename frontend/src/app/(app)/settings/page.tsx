"use client";

import { useState, useEffect } from "react";
import {
  Settings,
  User,
  Shield,
  Palette,
  CreditCard,
  Bell,
  LogOut,
  Brain
} from "lucide-react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { ListItemSkeleton } from "@/components/ui/skeleton";
import { showToast } from "@/components/ui/toast";

export default function SettingsPage() {
  const { data: user, loading } = useApi({
    fetcher: () => api.getMe(),
    errorMessage: "Failed to load user profile",
  });

  const handleLogout = () => {
    localStorage.removeItem("brain_token");
    window.location.href = "/login";
  };

  interface SettingField {
    label: string;
    value: string;
    type: "text" | "badge" | "toggle" | "action";
    actionText?: string;
    active?: boolean;
  }

  interface SettingSection {
    title: string;
    icon: any;
    color: string;
    bg: string;
    fields: SettingField[];
  }

  const sections: SettingSection[] = [
    {
      title: "Profile",
      icon: User,
      color: "text-violet-400",
      bg: "bg-violet-500/10 border-violet-500/20",
      fields: [
        { label: "Email", value: user?.email || "—", type: "text" },
        { label: "Full Name", value: user?.full_name || "Not set", type: "text" },
        { label: "Role", value: user?.role || "free", type: "badge" },
      ],
    },
    {
      title: "Security",
      icon: Shield,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10 border-emerald-500/20",
      fields: [
        { label: "Password", value: "••••••••", type: "action", actionText: "Change" },
        { label: "Multi-factor Auth", value: user?.is_mfa_enabled ? "Enabled" : "Disabled", type: "toggle", active: user?.is_mfa_enabled },
        { label: "API Keys", value: "0 active", type: "action", actionText: "Manage" },
      ],
    },
    {
      title: "Preferences",
      icon: Palette,
      color: "text-amber-400",
      bg: "bg-amber-500/10 border-amber-500/20",
      fields: [
        { label: "Theme", value: "Dark", type: "badge" },
        { label: "Communication Style", value: "Balanced", type: "text" },
        { label: "Auto-learn", value: "Enabled", type: "toggle", active: true },
      ],
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            Account Settings
            <div className="status-pulse w-2 h-2 rounded-full bg-violet-400 ml-2" />
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Manage your account and Brain preferences
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-4 py-2.5 bg-zinc-900/50 hover:bg-red-500/10 text-zinc-400 hover:text-red-400 border border-zinc-800/50 hover:border-red-500/30 rounded-xl font-medium text-sm transition-all shadow-sm group"
        >
          <LogOut className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
          Sign Out
        </button>
      </div>

      <div className="grid gap-6">
        {loading ? (
          <>
            <ListItemSkeleton />
            <ListItemSkeleton />
            <ListItemSkeleton />
          </>
        ) : (
          sections.map((section, idx) => {
            const Icon = section.icon;
            return (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                key={section.title} 
                className="glass card-hover border-zinc-800/50 rounded-2xl overflow-hidden"
              >
                <div className="flex items-center gap-3 px-6 py-4 border-b border-zinc-800/50 bg-zinc-900/20">
                  <div className={`w-8 h-8 rounded-lg ${section.bg} border flex items-center justify-center shadow-sm shrink-0`}>
                    <Icon className={`w-4 h-4 ${section.color}`} />
                  </div>
                  <h2 className="text-base font-semibold text-zinc-100">{section.title}</h2>
                </div>
                <div className="divide-y divide-zinc-800/50">
                  {section.fields.map((field) => (
                    <div
                      key={field.label}
                      className="flex flex-col sm:flex-row sm:items-center justify-between px-6 py-4 gap-4 sm:gap-0 hover:bg-zinc-800/20 transition-colors"
                    >
                      <span className="text-sm font-medium text-zinc-400">{field.label}</span>
                      <div className="flex items-center gap-3">
                        {field.type === "badge" ? (
                          <span className="text-xs font-bold uppercase tracking-wider bg-[var(--gradient-primary)] text-zinc-950 px-3 py-1 rounded-md shadow-[var(--shadow-glow)]">
                            {field.value}
                          </span>
                        ) : field.type === "toggle" ? (
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-zinc-300">{field.value}</span>
                            <div className={`w-10 h-5 rounded-full relative cursor-pointer transition-colors shadow-inner ${field.active ? 'bg-teal-500' : 'bg-zinc-700'}`}>
                              <div className={`w-3.5 h-3.5 bg-white rounded-full absolute top-[3px] transition-all shadow-sm ${field.active ? 'right-1' : 'left-1'}`} />
                            </div>
                          </div>
                        ) : field.type === "action" ? (
                          <div className="flex items-center gap-4">
                            <span className="text-sm text-zinc-300 font-mono">{field.value}</span>
                            <button className="text-xs font-semibold text-violet-400 hover:text-violet-300 transition-colors">
                              {field.actionText}
                            </button>
                          </div>
                        ) : (
                          <span className="text-sm font-medium text-zinc-200">{field.value}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            );
          })
        )}
      </div>

      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="text-center text-xs font-medium text-zinc-600 pt-8 pb-4"
      >
        <p className="flex items-center justify-center gap-2">
          <Brain className="w-4 h-4 text-zinc-500" />
          Brain AGI Platform v0.1.0 — Built with human-in-the-loop safety
        </p>
      </motion.div>
    </div>
  );
}
