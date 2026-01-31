/**
 * NEURAXIS - Skeleton Loading Components
 * Consistent loading state skeletons for various UI elements
 */

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

/**
 * Base skeleton element
 */
export function Skeleton({ className }: SkeletonProps) {
  return <div className={cn("animate-pulse rounded bg-muted", className)} />;
}

/**
 * Skeleton with shimmer effect
 */
export function SkeletonShimmer({ className }: SkeletonProps) {
  return (
    <div
      className={cn("rounded overflow-hidden relative", "bg-muted", className)}
    >
      <div
        className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite]"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)",
        }}
      />
    </div>
  );
}

/**
 * Skeleton text line
 */
export function SkeletonText({
  className,
  lines = 1,
}: SkeletonProps & { lines?: number }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn("h-4", i === lines - 1 && lines > 1 && "w-3/4")}
        />
      ))}
    </div>
  );
}

/**
 * Skeleton avatar
 */
export function SkeletonAvatar({
  className,
  size = "md",
}: SkeletonProps & { size?: "sm" | "md" | "lg" | "xl" }) {
  const sizes = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
    xl: "h-16 w-16",
  };

  return <Skeleton className={cn("rounded-full", sizes[size], className)} />;
}

/**
 * Skeleton button
 */
export function SkeletonButton({
  className,
  size = "md",
}: SkeletonProps & { size?: "sm" | "md" | "lg" }) {
  const sizes = {
    sm: "h-8 w-20",
    md: "h-10 w-24",
    lg: "h-12 w-32",
  };

  return <Skeleton className={cn("rounded-md", sizes[size], className)} />;
}

/**
 * Skeleton input
 */
export function SkeletonInput({ className }: SkeletonProps) {
  return <Skeleton className={cn("h-10 w-full rounded-md", className)} />;
}

/**
 * Skeleton card - matches PatientCard layout
 */
export function SkeletonPatientCard({ className }: SkeletonProps) {
  return (
    <div className={cn("p-4 rounded-lg border bg-card", className)}>
      <div className="flex items-start gap-4">
        <SkeletonAvatar size="lg" />
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-36" />
        </div>
        <div className="hidden sm:block space-y-1">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-4 w-20" />
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton card - matches CaseCard layout
 */
export function SkeletonCaseCard({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "p-4 rounded-lg border-l-4 border-l-muted bg-card",
        className
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-5 w-20 rounded-full" />
          </div>
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-full" />
        </div>
        <Skeleton className="h-4 w-16" />
      </div>
      <div className="flex items-center justify-between mt-3 pt-3 border-t">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-32" />
      </div>
    </div>
  );
}

/**
 * Skeleton card - matches DiagnosisCard layout
 */
export function SkeletonDiagnosisCard({ className }: SkeletonProps) {
  return (
    <div className={cn("p-4 rounded-lg border bg-card", className)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-5 w-16" />
          </div>
          <Skeleton className="h-5 w-48" />
        </div>
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
      <div className="mt-4">
        <div className="flex items-center justify-between mb-1">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-12" />
        </div>
        <Skeleton className="h-2 w-full rounded-full" />
      </div>
      <div className="mt-3 pt-3 border-t">
        <Skeleton className="h-3 w-32 mb-2" />
        <div className="flex gap-1">
          <Skeleton className="h-5 w-16 rounded" />
          <Skeleton className="h-5 w-20 rounded" />
          <Skeleton className="h-5 w-14 rounded" />
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton dashboard stats grid
 */
export function SkeletonStatsGrid({
  className,
  count = 4,
}: SkeletonProps & { count?: number }) {
  return (
    <div className={cn("grid gap-4 grid-cols-2 lg:grid-cols-4", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="p-4 rounded-lg border bg-card">
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-8 w-16 mb-1" />
          <Skeleton className="h-3 w-20" />
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton list
 */
export function SkeletonList({
  className,
  count = 5,
  itemHeight = "h-16",
}: SkeletonProps & { count?: number; itemHeight?: string }) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className={cn("w-full rounded-lg", itemHeight)} />
      ))}
    </div>
  );
}

/**
 * Skeleton page header
 */
export function SkeletonPageHeader({ className }: SkeletonProps) {
  return (
    <div className={cn("mb-6", className)}>
      <div className="flex items-center gap-2 mb-2">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-4" />
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex gap-2">
          <SkeletonButton />
          <SkeletonButton />
        </div>
      </div>
    </div>
  );
}
