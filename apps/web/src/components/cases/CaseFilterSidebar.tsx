/**
 * NEURAXIS - Case Filter Sidebar
 * Faceted search sidebar for filtering cases
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";
import type {
  CaseFilters,
  CasePriority,
  CaseStatus,
  FilterFacets,
} from "@/types/case-dashboard";
import { PRIORITY_CONFIG, STATUS_CONFIG } from "@/types/case-dashboard";
import { useCallback, useState } from "react";

interface CaseFilterSidebarProps {
  filters: CaseFilters;
  facets: FilterFacets | null;
  onFilterChange: (filters: Partial<CaseFilters>) => void;
  onReset: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function CaseFilterSidebar({
  filters,
  facets,
  onFilterChange,
  onReset,
  isCollapsed = false,
  onToggleCollapse,
}: CaseFilterSidebarProps) {
  const [dateStart, setDateStart] = useState(filters.dateRange?.start || "");
  const [dateEnd, setDateEnd] = useState(filters.dateRange?.end || "");

  const handlePriorityToggle = useCallback(
    (priority: CasePriority) => {
      const current = filters.priority || [];
      const updated = current.includes(priority)
        ? current.filter((p) => p !== priority)
        : [...current, priority];
      onFilterChange({ priority: updated.length ? updated : undefined });
    },
    [filters.priority, onFilterChange]
  );

  const handleStatusToggle = useCallback(
    (status: CaseStatus) => {
      const current = filters.status || [];
      const updated = current.includes(status)
        ? current.filter((s) => s !== status)
        : [...current, status];
      onFilterChange({ status: updated.length ? updated : undefined });
    },
    [filters.status, onFilterChange]
  );

  const handleDoctorToggle = useCallback(
    (doctorId: string) => {
      const current = filters.assignedTo || [];
      const updated = current.includes(doctorId)
        ? current.filter((d) => d !== doctorId)
        : [...current, doctorId];
      onFilterChange({ assignedTo: updated.length ? updated : undefined });
    },
    [filters.assignedTo, onFilterChange]
  );

  const handleDateRangeApply = useCallback(() => {
    if (dateStart && dateEnd) {
      onFilterChange({ dateRange: { start: dateStart, end: dateEnd } });
    }
  }, [dateStart, dateEnd, onFilterChange]);

  const handleDateRangeClear = useCallback(() => {
    setDateStart("");
    setDateEnd("");
    onFilterChange({ dateRange: undefined });
  }, [onFilterChange]);

  const activeFilterCount = [
    filters.priority?.length,
    filters.status?.length,
    filters.assignedTo?.length,
    filters.dateRange ? 1 : 0,
  ].filter(Boolean).length;

  if (isCollapsed) {
    return (
      <div className="w-12 border-r bg-card flex flex-col items-center py-4">
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-lg hover:bg-muted transition-colors"
          title="Expand filters"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="4" y1="21" x2="4" y2="14" />
            <line x1="4" y1="10" x2="4" y2="3" />
            <line x1="12" y1="21" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12" y2="3" />
            <line x1="20" y1="21" x2="20" y2="16" />
            <line x1="20" y1="12" x2="20" y2="3" />
            <line x1="1" y1="14" x2="7" y2="14" />
            <line x1="9" y1="8" x2="15" y2="8" />
            <line x1="17" y1="16" x2="23" y2="16" />
          </svg>
          {activeFilterCount > 0 && (
            <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-primary text-xs text-primary-foreground flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="w-64 border-r bg-card flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="font-semibold">Filters</h3>
        <div className="flex items-center gap-1">
          {activeFilterCount > 0 && (
            <Button size="sm" variant="ghost" onClick={onReset}>
              Clear all
            </Button>
          )}
          {onToggleCollapse && (
            <button
              onClick={onToggleCollapse}
              className="p-1.5 rounded hover:bg-muted transition-colors"
            >
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="11 17 6 12 11 7" />
                <polyline points="18 17 13 12 18 7" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Priority filter */}
        <div>
          <h4 className="text-sm font-medium mb-3">Priority</h4>
          <div className="space-y-2">
            {(["critical", "high", "moderate", "low"] as CasePriority[]).map(
              (priority) => {
                const config = PRIORITY_CONFIG[priority];
                const count =
                  facets?.priorities.find((p) => p.value === priority)?.count ||
                  0;
                const isActive = filters.priority?.includes(priority);

                return (
                  <label
                    key={priority}
                    className={cn(
                      "flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors",
                      isActive ? "bg-primary/10" : "hover:bg-muted"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => handlePriorityToggle(priority)}
                      className="sr-only"
                    />
                    <div
                      className={cn(
                        "h-4 w-4 rounded border-2 flex items-center justify-center",
                        isActive
                          ? "bg-primary border-primary"
                          : "border-muted-foreground/50"
                      )}
                    >
                      {isActive && (
                        <svg
                          className="h-2.5 w-2.5 text-primary-foreground"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </div>
                    <div
                      className={cn(
                        "h-2 w-2 rounded-full",
                        config.bgColor.replace("/10", "")
                      )}
                    />
                    <span className="flex-1 text-sm">{config.label}</span>
                    <span className="text-xs text-muted-foreground">
                      {count}
                    </span>
                  </label>
                );
              }
            )}
          </div>
        </div>

        {/* Status filter */}
        <div>
          <h4 className="text-sm font-medium mb-3">Status</h4>
          <div className="space-y-2">
            {(
              ["pending", "in_progress", "review", "completed"] as CaseStatus[]
            ).map((status) => {
              const config = STATUS_CONFIG[status];
              const count =
                facets?.statuses.find((s) => s.value === status)?.count || 0;
              const isActive = filters.status?.includes(status);

              return (
                <label
                  key={status}
                  className={cn(
                    "flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors",
                    isActive ? "bg-primary/10" : "hover:bg-muted"
                  )}
                >
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={() => handleStatusToggle(status)}
                    className="sr-only"
                  />
                  <div
                    className={cn(
                      "h-4 w-4 rounded border-2 flex items-center justify-center",
                      isActive
                        ? "bg-primary border-primary"
                        : "border-muted-foreground/50"
                    )}
                  >
                    {isActive && (
                      <svg
                        className="h-2.5 w-2.5 text-primary-foreground"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                  </div>
                  <span className="flex-1 text-sm">{config.label}</span>
                  <span className="text-xs text-muted-foreground">{count}</span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Date range filter */}
        <div>
          <h4 className="text-sm font-medium mb-3">Date Range</h4>
          <div className="space-y-2">
            <div>
              <label className="text-xs text-muted-foreground">From</label>
              <Input
                type="date"
                value={dateStart}
                onChange={(e) => setDateStart(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground">To</label>
              <Input
                type="date"
                value={dateEnd}
                onChange={(e) => setDateEnd(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={handleDateRangeClear}
                disabled={!filters.dateRange}
                className="flex-1"
              >
                Clear
              </Button>
              <Button
                size="sm"
                onClick={handleDateRangeApply}
                disabled={!dateStart || !dateEnd}
                className="flex-1"
              >
                Apply
              </Button>
            </div>
          </div>
        </div>

        {/* Assigned doctor filter */}
        {facets?.doctors && facets.doctors.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-3">Assigned To</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {facets.doctors.map((doctor) => {
                const isActive = filters.assignedTo?.includes(doctor.id);

                return (
                  <label
                    key={doctor.id}
                    className={cn(
                      "flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors",
                      isActive ? "bg-primary/10" : "hover:bg-muted"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => handleDoctorToggle(doctor.id)}
                      className="sr-only"
                    />
                    <div
                      className={cn(
                        "h-4 w-4 rounded border-2 flex items-center justify-center",
                        isActive
                          ? "bg-primary border-primary"
                          : "border-muted-foreground/50"
                      )}
                    >
                      {isActive && (
                        <svg
                          className="h-2.5 w-2.5 text-primary-foreground"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </div>
                    <span className="flex-1 text-sm truncate">
                      Dr. {doctor.name}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {doctor.count}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CaseFilterSidebar;
