"use client";

import Link from "next/link";
import { useRef } from "react";
import { Brain, MessageSquare, Database, ListChecks, Cpu, ArrowRight, Zap } from "lucide-react";
import NeuralMesh from "@/components/NeuralMesh";
import { useMotion, useMagnetic } from "@/lib/motion";

const FEATURES = [
  {
    icon: Brain,
    title: "Reason & Plan",
    body: "Break any goal into executable steps. The Executive Brain decomposes intent and orchestrates specialised agents to act on it.",
    accent: "text-signal",
  },
  {
    icon: Database,
    title: "Remember",
    body: "1,204 memory nodes and growing. Semantic, episodic, and procedural memory persist across every session — your AGI compounds.",
    accent: "text-ion",
  },
  {
    icon: MessageSquare,
    title: "Converse",
    body: "A chat surface wired to the same brain. Ask, instruct, and review — every exchange strengthens the model of you.",
    accent: "text-teal",
  },
  {
    icon: ListChecks,
    title: "Execute Tasks",
    body: "Background tasks run autonomously — optimise a database, scrape a target, run a security scan. You get the result, not the busywork.",
    accent: "text-signal",
  },
];

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/memory", label: "Memory" },
  { href: "/tasks", label: "Tasks" },
  { href: "/brain", label: "Brain Settings" },
];

export default function LandingPage() {
  useMotion();
  const ctaRef = useRef<HTMLAnchorElement>(null);
  useMagnetic(ctaRef, 0.3);

  return (
    <div className="relative min-h-screen bg-[var(--ink)] text-[var(--bone)] overflow-x-hidden">
      <NeuralMesh />

      {/* ambient corner glows */}
      <div className="pointer-events-none absolute -top-40 -left-32 w-[40rem] h-[40rem] rounded-full bg-[var(--glow-ion)] blur-[140px]" />
      <div className="pointer-events-none absolute top-1/3 -right-40 w-[36rem] h-[36rem] rounded-full bg-[var(--glow-signal)] blur-[150px] opacity-70" />

      {/* ── top bar ── */}
      <header className="relative z-20 flex items-center justify-between px-6 md:px-10 py-5 max-w-7xl mx-auto">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <span className="w-9 h-9 rounded-xl bg-[var(--gradient-primary)] p-[1px] shadow-[var(--shadow-glow)] transition-transform duration-300 group-hover:scale-105">
            <span className="w-full h-full bg-[var(--ink)] rounded-[11px] flex items-center justify-center">
              <Brain className="w-4 h-4 text-signal" />
            </span>
          </span>
          <span className="font-display font-semibold tracking-tight text-[var(--bone)]">
            Brain<span className="text-signal">AGI</span>
          </span>
        </Link>
        <nav className="hidden md:flex items-center gap-8">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="text-sm text-[var(--bone-soft)] hover:text-[var(--signal)] transition-colors"
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <Link href="/login" className="btn-ghost !py-2 !px-5 text-sm">
          Sign in
        </Link>
      </header>

      {/* ── hero ── */}
      <section className="relative z-10 px-6 md:px-10 pt-16 md:pt-28 pb-24 max-w-7xl mx-auto">
        <div className="hero-rise d1 inline-flex items-center gap-2 rounded-full border border-[var(--hairline-strong)] px-4 py-1.5 mb-8">
          <span className="status-dot w-2 h-2 rounded-full bg-teal" />
          <span className="font-mono text-xs tracking-widest uppercase text-[var(--bone-soft)]">
            Live · 99.9% brain sync
          </span>
        </div>

        <h1 className="hero-rise d2 font-display font-bold leading-[0.95] tracking-tight text-[var(--bone)] max-w-4xl text-[clamp(2.8rem,8vw,6.5rem)]">
          Your AGI
          <br />
          <span className="bg-[var(--gradient-primary)] bg-clip-text text-transparent">
            platform
          </span>
        </h1>

        <p className="hero-rise d3 mt-7 max-w-xl text-lg text-[var(--bone-soft)] leading-relaxed">
          It thinks, plans, remembers, and builds. An autonomous system that
          reasons over your goals and executes them — while you watch the
          cortex fire.
        </p>

        <div className="hero-rise d4 mt-10 flex flex-col sm:flex-row gap-4">
          <Link ref={ctaRef} href="/login" className="btn-primary magnetic">
            Enter Platform
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="/dashboard" className="btn-ghost">
            <Zap className="w-4 h-4 text-signal" />
            View Mission Control
          </Link>
        </div>

        {/* live telemetry ticker */}
        <div className="hero-rise d4 mt-16 flex flex-wrap items-center gap-x-8 gap-y-3 font-mono text-xs text-[var(--muted)]">
          <span><span className="text-signal">1,204</span> memory nodes</span>
          <span className="text-[var(--hairline-strong)]">·</span>
          <span><span className="text-ion">3</span> active tasks</span>
          <span className="text-[var(--hairline-strong)]">·</span>
          <span><span className="text-teal">Optimal</span> system health</span>
        </div>
      </section>

      {/* ── features ── */}
      <section className="relative z-10 px-6 md:px-10 py-24 max-w-7xl mx-auto">
        <div data-reveal className="reveal mb-14">
          <p className="eyebrow mb-4">What it does</p>
          <h2 className="font-display text-3xl md:text-5xl font-bold tracking-tight max-w-2xl">
            A control room for an autonomous mind.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {FEATURES.map((f, i) => (
            <article
              key={f.title}
              data-reveal
              className="reveal tilt instrument ticks p-8 md:p-10 group"
              style={{ transitionDelay: `${i * 0.05}s` }}
            >
              <div className="tilt-inner">
                <div className="flex items-center justify-between mb-6">
                  <span className={`w-12 h-12 rounded-xl border border-[var(--hairline-strong)] bg-[var(--panel-2)] flex items-center justify-center ${f.accent}`}>
                    <f.icon className="w-5 h-5" />
                  </span>
                  <span className="font-mono text-xs text-[var(--muted)]">
                    0{i + 1}
                  </span>
                </div>
                <h3 className="font-display text-xl font-semibold mb-3 text-[var(--bone)] group-hover:text-[var(--signal)] transition-colors">
                  {f.title}
                </h3>
                <p className="text-[var(--bone-soft)] leading-relaxed text-sm md:text-base">
                  {f.body}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ── CTA band ── */}
      <section className="relative z-10 px-6 md:px-10 pb-28 max-w-7xl mx-auto">
        <div
          data-reveal
          className="reveal instrument ticks relative overflow-hidden rounded-3xl p-10 md:p-16 text-center"
        >
          <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-[30rem] h-[30rem] rounded-full bg-[var(--glow-signal)] blur-[120px]" />
          <p className="eyebrow mb-4">Start now</p>
          <h2 className="font-display text-3xl md:text-5xl font-bold tracking-tight max-w-2xl mx-auto">
            Give your goals a brain.
          </h2>
          <p className="mt-5 text-[var(--bone-soft)] max-w-md mx-auto">
            Sign in to spin up your AGI platform. No setup, no config — it
            remembers you.
          </p>
          <Link href="/login" className="btn-primary mt-9 inline-flex">
            Enter Platform
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ── footer ── */}
      <footer className="relative z-10 border-t border-[var(--hairline)] px-6 md:px-10 py-8 max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-[var(--muted)]">
        <span className="font-display font-semibold text-[var(--bone-soft)]">
          Brain<span className="text-signal">AGI</span>
        </span>
        <span className="font-mono text-xs">Secured by AGI Core</span>
        <div className="flex gap-6">
          <Link href="/dashboard" className="hover:text-[var(--signal)] transition-colors">Dashboard</Link>
          <Link href="/memory" className="hover:text-[var(--signal)] transition-colors">Memory</Link>
          <Link href="/tasks" className="hover:text-[var(--signal)] transition-colors">Tasks</Link>
        </div>
      </footer>
    </div>
  );
}
