/**
 * NEURAXIS - Patient List Loading Skeleton
 * Loading state for patient list page
 */

import { DashboardLayout, PageHeader } from "@/components/layout/Layout";
import { SkeletonTable } from "@/components/ui/Skeleton";

export default function PatientsLoading() {
  return (
    <DashboardLayout>
      <PageHeader
        title="Patients"
        description="Loading patients..."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Patients" },
        ]}
      />

      <div className="flex gap-6 mt-6">
        {/* Filter sidebar skeleton */}
        <aside className="w-64 border-r bg-card flex flex-col">
          <div className="px-4 py-3 border-b">
            <div className="h-5 w-20 bg-muted rounded animate-pulse" />
          </div>
          <div className="p-4 space-y-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-3">
                <div className="h-4 w-16 bg-muted rounded animate-pulse" />
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, j) => (
                    <div key={j} className="flex items-center gap-2">
                      <div className="h-4 w-4 bg-muted rounded animate-pulse" />
                      <div className="h-3 flex-1 bg-muted rounded animate-pulse" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Main content skeleton */}
        <div className="flex-1 min-w-0">
          {/* Search skeleton */}
          <div className="mb-6 space-y-4">
            <div className="h-10 max-w-xl bg-muted rounded-md animate-pulse" />
            <div className="flex gap-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="h-8 w-16 bg-muted rounded-full animate-pulse"
                />
              ))}
            </div>
          </div>

          {/* Table skeleton */}
          <SkeletonTable columns={8} rows={10} showHeader />
        </div>
      </div>
    </DashboardLayout>
  );
}
