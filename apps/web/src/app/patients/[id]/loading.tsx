/**
 * NEURAXIS - Patient Profile Loading State
 * Skeleton loading for patient profile page
 */

import { DashboardLayout } from "@/components/layout/Layout";

export default function PatientProfileLoading() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        {/* Breadcrumb skeleton */}
        <div className="flex gap-2 mb-2">
          <div className="h-4 w-20 bg-muted rounded" />
          <span className="text-muted-foreground">/</span>
          <div className="h-4 w-16 bg-muted rounded" />
          <span className="text-muted-foreground">/</span>
          <div className="h-4 w-32 bg-muted rounded" />
        </div>

        {/* Title skeleton */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="h-8 w-48 bg-muted rounded mb-2" />
            <div className="h-4 w-32 bg-muted rounded" />
          </div>
          <div className="flex gap-2">
            <div className="h-10 w-24 bg-muted rounded" />
            <div className="h-10 w-28 bg-muted rounded" />
            <div className="h-10 w-28 bg-muted rounded" />
          </div>
        </div>

        {/* Header card skeleton */}
        <div className="p-6 rounded-xl border bg-card mb-6">
          <div className="flex gap-6">
            {/* Avatar */}
            <div className="flex flex-col items-center">
              <div className="h-24 w-24 rounded-full bg-muted mb-3" />
              <div className="h-6 w-16 bg-muted rounded-full" />
            </div>

            {/* Demographics grid */}
            <div className="flex-1 grid grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i}>
                  <div className="h-3 w-16 bg-muted rounded mb-2" />
                  <div className="h-4 w-24 bg-muted rounded" />
                </div>
              ))}
            </div>

            {/* Quick actions */}
            <div className="flex flex-col gap-2">
              <div className="h-9 w-20 bg-muted rounded" />
              <div className="h-9 w-20 bg-muted rounded" />
              <div className="h-9 w-20 bg-muted rounded" />
            </div>
          </div>

          {/* Emergency contact */}
          <div className="mt-4 pt-4 border-t flex gap-6">
            <div className="h-4 w-64 bg-muted rounded" />
            <div className="h-4 w-48 bg-muted rounded" />
          </div>
        </div>

        {/* Tabs skeleton */}
        <div className="flex gap-2 mb-6">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="h-10 w-24 bg-muted rounded" />
          ))}
        </div>

        {/* Content skeleton */}
        <div className="grid grid-cols-3 gap-6">
          {/* Main column */}
          <div className="col-span-2 space-y-6">
            {/* Allergies & conditions */}
            <div className="grid grid-cols-2 gap-6">
              <div className="h-48 bg-muted rounded-lg" />
              <div className="h-48 bg-muted rounded-lg" />
            </div>

            {/* Vitals chart */}
            <div className="h-80 bg-muted rounded-lg" />

            {/* Timeline */}
            <div className="h-64 bg-muted rounded-lg" />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="h-48 bg-muted rounded-lg" />
            <div className="h-56 bg-muted rounded-lg" />
            <div className="h-48 bg-muted rounded-lg" />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
