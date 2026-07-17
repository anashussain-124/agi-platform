"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn("shimmer rounded-lg", className)} />
  );
}

/** Pre-built skeleton for a stat card */
export function StatSkeleton() {
  return (
    <div className="p-5 rounded-2xl bg-zinc-900/50 border border-zinc-800/50 flex items-start gap-4">
      <Skeleton className="w-12 h-12 rounded-xl" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-7 w-16" />
      </div>
    </div>
  );
}

/** Pre-built skeleton for a list item */
export function ListItemSkeleton() {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 flex items-center gap-3">
      <Skeleton className="w-6 h-6 rounded-md" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-3 w-32" />
      </div>
      <Skeleton className="h-5 w-16 rounded-full" />
    </div>
  );
}

/** Pre-built skeleton for a chat message */
export function MessageSkeleton() {
  return (
    <div className="flex gap-4">
      <Skeleton className="w-8 h-8 rounded-full shrink-0" />
      <div className="flex-1 space-y-2 max-w-[60%]">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    </div>
  );
}
