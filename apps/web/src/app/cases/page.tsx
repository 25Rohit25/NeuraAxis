/**
 * NEURAXIS - Case Dashboard Page
 * Main dashboard for doctors to manage their cases
 */

"use client";

import { BulkActionsToolbar } from "@/components/cases/BulkActionsToolbar";
import { CaseCard, CompactCaseCard } from "@/components/cases/CaseCard";
import { CaseFilterSidebar } from "@/components/cases/CaseFilterSidebar";
import {
  NotificationBell,
  ToastNotification,
} from "@/components/cases/CaseNotifications";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  useCaseDashboard,
  useRealtimeCases,
  useVirtualScroll,
} from "@/hooks/useCaseDashboard";
import { cn, debounce } from "@/lib/utils";
import type {
  CaseEvent,
  CaseNotification,
  CaseSortOptions,
  CaseSummary,
  DashboardView,
} from "@/types/case-dashboard";
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useRef, useState } from "react";

// =============================================================================
// Dashboard View Tabs
// =============================================================================

interface ViewTab {
  id: DashboardView;
  label: string;
  icon: React.ReactNode;
}

const VIEW_TABS: ViewTab[] = [
  {
    id: "active",
    label: "My Active Cases",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    ),
  },
  {
    id: "urgent",
    label: "Urgent",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
  },
  {
    id: "pending",
    label: "Pending Review",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
  },
  {
    id: "closed",
    label: "Recently Closed",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
  },
  {
    id: "team",
    label: "Team Cases",
    icon: (
      <svg
        className="h-4 w-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
];

// =============================================================================
// Stats Cards
// =============================================================================

interface StatsCardsProps {
  stats: {
    activeCount: number;
    urgentCount: number;
    pendingReviewCount: number;
    completedToday: number;
    avgResolutionTime: number;
    totalThisWeek: number;
  } | null;
  isLoading: boolean;
}

function StatsCards({ stats, isLoading }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const statItems = [
    { label: "Active Cases", value: stats.activeCount, color: "text-primary" },
    {
      label: "Urgent",
      value: stats.urgentCount,
      color: "text-danger",
      pulse: stats.urgentCount > 0,
    },
    {
      label: "Pending Review",
      value: stats.pendingReviewCount,
      color: "text-warning",
    },
    {
      label: "Completed Today",
      value: stats.completedToday,
      color: "text-success",
    },
    {
      label: "Avg Resolution",
      value: `${stats.avgResolutionTime}h`,
      color: "text-info",
    },
    {
      label: "This Week",
      value: stats.totalThisWeek,
      color: "text-muted-foreground",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      {statItems.map((item) => (
        <div
          key={item.label}
          className="bg-card rounded-xl border p-4 hover:shadow-md transition-shadow"
        >
          <p className="text-sm text-muted-foreground">{item.label}</p>
          <p
            className={cn(
              "text-2xl font-bold mt-1",
              item.color,
              item.pulse && "animate-pulse"
            )}
          >
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// Virtual Case List
// =============================================================================

interface VirtualCaseListProps {
  cases: CaseSummary[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onOpenCase: (id: string) => void;
  onAssign: (id: string) => void;
  onArchive: (id: string) => void;
  viewMode: "grid" | "list";
  isLoading: boolean;
  hasMore: boolean;
  onLoadMore: () => void;
}

function VirtualCaseList({
  cases,
  selectedIds,
  onToggleSelect,
  onOpenCase,
  onAssign,
  onArchive,
  viewMode,
  isLoading,
  hasMore,
  onLoadMore,
}: VirtualCaseListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerHeight, setContainerHeight] = useState(600);

  // Update container height on resize
  useEffect(() => {
    const updateHeight = () => {
      if (containerRef.current) {
        setContainerHeight(containerRef.current.clientHeight);
      }
    };

    updateHeight();
    window.addEventListener("resize", updateHeight);
    return () => window.removeEventListener("resize", updateHeight);
  }, []);

  const itemHeight = viewMode === "grid" ? 280 : 64;
  const { visibleItems, totalHeight, handleScroll } = useVirtualScroll(cases, {
    itemHeight,
    containerHeight,
    overscan: 5,
  });

  // Infinite scroll trigger
  const handleScrollWithInfinite = useCallback(
    (e: React.UIEvent<HTMLElement>) => {
      handleScroll(e);

      const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
      if (
        scrollHeight - scrollTop - clientHeight < 200 &&
        hasMore &&
        !isLoading
      ) {
        onLoadMore();
      }
    },
    [handleScroll, hasMore, isLoading, onLoadMore]
  );

  if (isLoading && cases.length === 0) {
    return (
      <div
        className={cn(
          "grid gap-4",
          viewMode === "grid"
            ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
            : "grid-cols-1"
        )}
      >
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className={viewMode === "grid" ? "h-64" : "h-16"} />
        ))}
      </div>
    );
  }

  if (cases.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <svg
          className="h-16 w-16 text-muted-foreground/50 mb-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
        <h3 className="text-lg font-medium mb-1">No cases found</h3>
        <p className="text-muted-foreground">
          Try adjusting your filters or search query
        </p>
      </div>
    );
  }

  // For grid view, use standard layout (virtual scroll for list view)
  if (viewMode === "grid") {
    return (
      <div
        ref={containerRef}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto"
        style={{ maxHeight: "calc(100vh - 300px)" }}
        onScroll={(e) => {
          const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
          if (
            scrollHeight - scrollTop - clientHeight < 200 &&
            hasMore &&
            !isLoading
          ) {
            onLoadMore();
          }
        }}
      >
        {cases.map((caseData) => (
          <CaseCard
            key={caseData.id}
            caseData={caseData}
            isSelected={selectedIds.has(caseData.id)}
            onSelect={() => onToggleSelect(caseData.id)}
            onOpen={() => onOpenCase(caseData.id)}
            onAssign={() => onAssign(caseData.id)}
            onArchive={() => onArchive(caseData.id)}
          />
        ))}
        {isLoading && (
          <>
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
          </>
        )}
      </div>
    );
  }

  // List view with virtual scrolling
  return (
    <div
      ref={containerRef}
      className="bg-card rounded-xl border overflow-hidden"
      style={{ height: "calc(100vh - 300px)" }}
    >
      {/* List header */}
      <div className="flex items-center gap-4 px-4 py-3 border-b bg-muted/50 text-sm font-medium text-muted-foreground">
        <div className="w-4" /> {/* Checkbox space */}
        <div className="w-2" /> {/* Priority dot */}
        <div className="w-28">Case #</div>
        <div className="w-48">Patient</div>
        <div className="flex-1">Chief Complaint</div>
        <div className="w-24 text-center">Status</div>
        <div className="w-28">Assigned</div>
        <div className="w-20 text-right">Updated</div>
      </div>

      {/* Virtual list */}
      <div
        className="overflow-y-auto"
        style={{ height: containerHeight - 48 }}
        onScroll={handleScrollWithInfinite}
      >
        <div style={{ height: totalHeight, position: "relative" }}>
          {visibleItems.map(({ item, style }) => (
            <CompactCaseCard
              key={item.id}
              caseData={item}
              isSelected={selectedIds.has(item.id)}
              onSelect={() => onToggleSelect(item.id)}
              onOpen={() => onOpenCase(item.id)}
              style={style}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Dashboard Component
// =============================================================================

export default function CaseDashboardPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [isFilterCollapsed, setIsFilterCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [toastNotifications, setToastNotifications] = useState<
    CaseNotification[]
  >([]);

  // Dashboard data hook
  const dashboard = useCaseDashboard({ initialView: "active", pageSize: 20 });

  // Real-time updates hook
  const realtime = useRealtimeCases({
    onCaseEvent: (event: CaseEvent) => {
      // Refresh cases on relevant events
      if (
        ["case_created", "case_assigned", "case_status_changed"].includes(
          event.type
        )
      ) {
        dashboard.refreshCases();
      }
    },
    onNotification: (notification: CaseNotification) => {
      // Show toast notification
      setToastNotifications((prev) => [...prev, notification]);
    },
  });

  // Debounced search
  const debouncedSearch = useCallback(
    debounce((query: string) => {
      dashboard.setFilters({ search: query || undefined });
    }, 300),
    [dashboard.setFilters]
  );

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    debouncedSearch(e.target.value);
  };

  const handleViewChange = (view: DashboardView) => {
    dashboard.setFilters({ view });
  };

  const handleSortChange = (sort: CaseSortOptions) => {
    dashboard.setSort(sort);
  };

  const handleOpenCase = (caseId: string) => {
    router.push(`/cases/${caseId}`);
  };

  const handleAssignCase = (caseId: string) => {
    // Open assign modal - for now just log
    console.log("Assign case:", caseId);
  };

  const handleArchiveCase = async (caseId: string) => {
    await dashboard.archiveCase(caseId);
  };

  const handleBulkAction = async (action: string, options?: any) => {
    const payload = {
      caseIds: Array.from(dashboard.selectedIds),
      action: action as any,
      ...options,
    };
    await dashboard.executeBulkAction(payload);
  };

  const dismissToast = (id: string) => {
    setToastNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur">
        <div className="flex items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-2xl font-bold">Case Dashboard</h1>
            <p className="text-sm text-muted-foreground">
              Manage and monitor your medical cases
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Connection status */}
            <div
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs",
                realtime.isConnected
                  ? "bg-success/10 text-success"
                  : "bg-warning/10 text-warning"
              )}
            >
              <div
                className={cn(
                  "h-2 w-2 rounded-full",
                  realtime.isConnected
                    ? "bg-success"
                    : "bg-warning animate-pulse"
                )}
              />
              {realtime.isConnected ? "Live" : "Connecting..."}
            </div>

            {/* Notifications */}
            <NotificationBell
              notifications={realtime.notifications}
              unreadCount={realtime.unreadCount}
              onMarkAsRead={realtime.markAsRead}
              onMarkAllAsRead={realtime.markAllAsRead}
              onClear={realtime.clearNotifications}
              onNotificationClick={(n) => handleOpenCase(n.caseId)}
            />

            {/* New case button */}
            <Button onClick={() => router.push("/cases/new")}>
              <svg
                className="h-4 w-4 mr-2"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New Case
            </Button>
          </div>
        </div>

        {/* View tabs */}
        <div className="px-6 pb-4">
          <div className="flex items-center gap-1 p-1 bg-muted rounded-lg w-fit">
            {VIEW_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleViewChange(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors",
                  dashboard.filters.view === tab.id
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {tab.icon}
                {tab.label}
                {tab.id === "urgent" && dashboard.stats?.urgentCount ? (
                  <span className="h-5 min-w-[20px] px-1.5 rounded-full bg-danger text-white text-xs flex items-center justify-center">
                    {dashboard.stats.urgentCount}
                  </span>
                ) : null}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Filter sidebar */}
        <CaseFilterSidebar
          filters={dashboard.filters}
          facets={dashboard.facets}
          onFilterChange={dashboard.setFilters}
          onReset={dashboard.resetFilters}
          isCollapsed={isFilterCollapsed}
          onToggleCollapse={() => setIsFilterCollapsed(!isFilterCollapsed)}
        />

        {/* Main content */}
        <main className="flex-1 p-6">
          {/* Stats */}
          <div className="mb-6">
            <StatsCards
              stats={dashboard.stats}
              isLoading={dashboard.isLoading}
            />
          </div>

          {/* Toolbar */}
          <div className="flex items-center justify-between gap-4 mb-4">
            {/* Search */}
            <div className="relative w-80">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <Input
                placeholder="Search by patient, MRN, diagnosis..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="pl-10"
              />
            </div>

            <div className="flex items-center gap-3">
              {/* Sort dropdown */}
              <select
                value={`${dashboard.sort.field}-${dashboard.sort.direction}`}
                onChange={(e) => {
                  const [field, direction] = e.target.value.split("-") as [
                    any,
                    any,
                  ];
                  handleSortChange({ field, direction });
                }}
                className="h-10 px-3 rounded-lg border bg-background text-sm"
              >
                <option value="updatedAt-desc">Recently Updated</option>
                <option value="createdAt-desc">Newest First</option>
                <option value="createdAt-asc">Oldest First</option>
                <option value="priority-desc">Highest Priority</option>
                <option value="priority-asc">Lowest Priority</option>
                <option value="patientName-asc">Patient A-Z</option>
              </select>

              {/* View toggle */}
              <div className="flex items-center p-1 bg-muted rounded-lg">
                <button
                  onClick={() => setViewMode("grid")}
                  className={cn(
                    "p-2 rounded-md transition-colors",
                    viewMode === "grid"
                      ? "bg-background shadow-sm"
                      : "hover:bg-background/50"
                  )}
                  title="Grid view"
                >
                  <svg
                    className="h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect x="3" y="3" width="7" height="7" />
                    <rect x="14" y="3" width="7" height="7" />
                    <rect x="14" y="14" width="7" height="7" />
                    <rect x="3" y="14" width="7" height="7" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode("list")}
                  className={cn(
                    "p-2 rounded-md transition-colors",
                    viewMode === "list"
                      ? "bg-background shadow-sm"
                      : "hover:bg-background/50"
                  )}
                  title="List view"
                >
                  <svg
                    className="h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="8" y1="6" x2="21" y2="6" />
                    <line x1="8" y1="12" x2="21" y2="12" />
                    <line x1="8" y1="18" x2="21" y2="18" />
                    <line x1="3" y1="6" x2="3.01" y2="6" />
                    <line x1="3" y1="12" x2="3.01" y2="12" />
                    <line x1="3" y1="18" x2="3.01" y2="18" />
                  </svg>
                </button>
              </div>

              {/* Export button */}
              <Button variant="outline" onClick={() => dashboard.exportCases()}>
                <svg
                  className="h-4 w-4 mr-2"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Export CSV
              </Button>
            </div>
          </div>

          {/* Results count */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted-foreground">
              {dashboard.totalCount} case{dashboard.totalCount !== 1 ? "s" : ""}{" "}
              found
            </p>
            {dashboard.error && (
              <p className="text-sm text-danger">{dashboard.error}</p>
            )}
          </div>

          {/* Case list */}
          <VirtualCaseList
            cases={dashboard.cases}
            selectedIds={dashboard.selectedIds}
            onToggleSelect={dashboard.toggleSelect}
            onOpenCase={handleOpenCase}
            onAssign={handleAssignCase}
            onArchive={handleArchiveCase}
            viewMode={viewMode}
            isLoading={dashboard.isLoading || dashboard.isLoadingMore}
            hasMore={dashboard.hasMore}
            onLoadMore={dashboard.loadMore}
          />
        </main>
      </div>

      {/* Bulk actions toolbar */}
      <BulkActionsToolbar
        selectedCount={dashboard.selectedIds.size}
        onClearSelection={dashboard.clearSelection}
        onSelectAll={dashboard.selectAll}
        totalCount={dashboard.totalCount}
        onAction={handleBulkAction}
        availableDoctors={[]}
      />

      {/* Toast notifications */}
      <div className="fixed bottom-6 right-6 z-50 space-y-3 w-80">
        {toastNotifications.slice(0, 3).map((notification) => (
          <ToastNotification
            key={notification.id}
            notification={notification}
            onDismiss={() => dismissToast(notification.id)}
            onClick={() => {
              handleOpenCase(notification.caseId);
              dismissToast(notification.id);
            }}
          />
        ))}
      </div>
    </div>
  );
}
