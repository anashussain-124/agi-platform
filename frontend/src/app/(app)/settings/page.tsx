"use client";

import { useState, useEffect } from "react";
import {
  Settings,
  User,
  Shield,
  Palette,
} from "lucide-react";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [user, setUser] = useState<{
    id: string;
    email: string;
    full_name: string | null;
    role: string;
    is_mfa_enabled: boolean;
  } | null>(null);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => {});
  }, []);

  const sections = [
    {
      title: "Profile",
      icon: User,
      fields: [
        { label: "Email", value: user?.email || "—", type: "text" },
        { label: "Full Name", value: user?.full_name || "Not set", type: "text" },
        { label: "Role", value: user?.role || "free", type: "badge" },
      ],
    },
    {
      title: "Security",
      icon: Shield,
      fields: [
        { label: "Password", value: "••••••••", type: "action" },
        { label: "Multi-factor Auth", value: "Disabled", type: "toggle" },
        { label: "API Keys", value: "0 active", type: "action" },
      ],
    },
    {
      title: "Preferences",
      icon: Palette,
      fields: [
        { label: "Theme", value: "Dark", type: "badge" },
        { label: "Communication Style", value: "Balanced", type: "select" },
        { label: "Auto-learn", value: "Enabled", type: "toggle" },
      ],
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Account Settings</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Manage your account and Brain preferences
        </p>
      </div>

      {sections.map((section) => {
        const Icon = section.icon;
        return (
          <div key={section.title} className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800">
              <Icon className="w-4 h-4 text-zinc-400" />
              <h2 className="text-sm font-semibold text-zinc-200">{section.title}</h2>
            </div>
            <div className="divide-y divide-zinc-800/50">
              {section.fields.map((field) => (
                <div
                  key={field.label}
                  className="flex items-center justify-between px-4 py-3"
                >
                  <span className="text-sm text-zinc-400">{field.label}</span>
                  <div className="flex items-center gap-2">
                    {field.type === "badge" ? (
                      <span className="text-xs bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded-full">
                        {field.value}
                      </span>
                    ) : field.type === "toggle" ? (
                      <div className="w-8 h-4 bg-teal-600 rounded-full relative cursor-pointer">
                        <div className="w-3 h-3 bg-white rounded-full absolute top-0.5 right-0.5" />
                      </div>
                    ) : (
                      <span className="text-sm text-zinc-200">{field.value}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      <div className="text-center text-xs text-zinc-600 py-4">
        Brain AGI Platform v0.1.0 — Built with human-in-the-loop safety
      </div>
    </div>
  );
}
