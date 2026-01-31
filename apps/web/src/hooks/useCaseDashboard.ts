/**
 * NEURAXIS - Case Dashboard Hooks
 * React hooks for case dashboard state and real-time updates
 */

"use client";

import type {
  BulkActionPayload,
  CaseEvent,
  CaseFilters,
  CaseNotification,
  CaseSortOptions,
  CaseSummary,
  DashboardStats,
  DashboardView,
  FilterFacets,
} from "@/types/case-dashboard";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

// =============================================================================
// Dashboard Data Hook
// =============================================================================

interface UseCaseDashboardOptions {
  initialView?: DashboardView;
  pageSize?: number;
  enableRealtime?: boolean;
}

interface UseCaseDashboardReturn {
  // Data
  cases: CaseSummary[];
  stats: DashboardStats | null;
  facets: FilterFacets | null;

  // Loading states
  isLoading: boolean;
  isLoadingMore: boolean;
  error: string | null;

  // Pagination
  page: number;
  totalPages: number;
  totalCount: number;
  hasMore: boolean;
  loadMore: () => void;

  // Filters & sorting
  filters: CaseFilters;
  setFilters: (filters: Partial<CaseFilters>) => void;
  resetFilters: () => void;
  sort: CaseSortOptions;
  setSort: (sort: CaseSortOptions) => void;

  // Selection
  selectedIds: Set<string>;
  toggleSelect: (id: string) => void;
  selectAll: () => void;
  clearSelection: () => void;

  // Actions
  refreshCases: () => void;
  executeBulkAction: (payload: BulkActionPayload) => Promise<void>;
  assignCase: (caseId: string, doctorId: string) => Promise<void>;
  updateCaseStatus: (caseId: string, status: string) => Promise<void>;
  archiveCase: (caseId: string) => Promise<void>;
  exportCases: (ids?: string[]) => Promise<void>;
}

const DEFAULT_FILTERS: CaseFilters = {
  view: "active",
};

const DEFAULT_SORT: CaseSortOptions = {
  field: "updatedAt",
  direction: "desc",
};

export function useCaseDashboard(
  options: UseCaseDashboardOptions = {}
): UseCaseDashboardReturn {
  const {
    initialView = "active",
    pageSize = 20,
    enableRealtime = true,
  } = options;

  // State
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [facets, setFacets] = useState<FilterFacets | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [filters, setFiltersState] = useState<CaseFilters>({
    ...DEFAULT_FILTERS,
    view: initialView,
  });
  const [sort, setSort] = useState<CaseSortOptions>(DEFAULT_SORT);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Refs
  const abortControllerRef = useRef<AbortController | null>(null);

  // Fetch cases
  const fetchCases = useCallback(
    async (pageNum: number = 1, append: boolean = false) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();

      if (append) {
        setIsLoadingMore(true);
      } else {
        setIsLoading(true);
      }
      setError(null);

      try {
        const params = new URLSearchParams({
          page: pageNum.toString(),
          pageSize: pageSize.toString(),
          view: filters.view,
          sortField: sort.field,
          sortDirection: sort.direction,
        });

        if (filters.priority?.length) {
          params.set("priority", filters.priority.join(","));
        }
        if (filters.status?.length) {
          params.set("status", filters.status.join(","));
        }
        if (filters.assignedTo?.length) {
          params.set("assignedTo", filters.assignedTo.join(","));
        }
        if (filters.search) {
          params.set("search", filters.search);
        }
        if (filters.dateRange) {
          params.set("dateStart", filters.dateRange.start);
          params.set("dateEnd", filters.dateRange.end);
        }

        const response = await fetch(`/api/cases/dashboard?${params}`, {
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) throw new Error("Failed to fetch cases");

        const data = await response.json();

        setCases((prev) => (append ? [...prev, ...data.cases] : data.cases));
        setTotalPages(data.totalPages);
        setTotalCount(data.total);
        setPage(pageNum);

        if (data.stats) setStats(data.stats);
        if (data.facets) setFacets(data.facets);
      } catch (err: any) {
        if (err.name !== "AbortError") {
          setError(err.message || "Failed to load cases");
        }
      } finally {
        setIsLoading(false);
        setIsLoadingMore(false);
      }
    },
    [filters, sort, pageSize]
  );

  // Effects
  useEffect(() => {
    fetchCases(1, false);
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [fetchCases]);

  // Filter setters
  const setFilters = useCallback((newFilters: Partial<CaseFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...newFilters }));
    setPage(1);
    setSelectedIds(new Set());
  }, []);

  const resetFilters = useCallback(() => {
    setFiltersState({ ...DEFAULT_FILTERS, view: filters.view });
    setPage(1);
    setSelectedIds(new Set());
  }, [filters.view]);

  // Pagination
  const loadMore = useCallback(() => {
    if (!isLoadingMore && page < totalPages) {
      fetchCases(page + 1, true);
    }
  }, [fetchCases, page, totalPages, isLoadingMore]);

  // Selection
  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedIds(new Set(cases.map((c) => c.id)));
  }, [cases]);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  // Actions
  const executeBulkAction = useCallback(
    async (payload: BulkActionPayload) => {
      try {
        const response = await fetch("/api/cases/bulk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) throw new Error("Bulk action failed");

        await fetchCases(1, false);
        clearSelection();
      } catch (err: any) {
        throw err;
      }
    },
    [fetchCases, clearSelection]
  );

  const assignCase = useCallback(async (caseId: string, doctorId: string) => {
    const response = await fetch(`/api/cases/${caseId}/assign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doctorId }),
    });

    if (!response.ok) throw new Error("Assignment failed");

    setCases((prev) =>
      prev.map((c) =>
        c.id === caseId
          ? { ...c, assignedTo: { ...c.assignedTo, id: doctorId } }
          : c
      )
    );
  }, []);

  const updateCaseStatus = useCallback(
    async (caseId: string, status: string) => {
      const response = await fetch(`/api/cases/${caseId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });

      if (!response.ok) throw new Error("Status update failed");

      await fetchCases(page, false);
    },
    [fetchCases, page]
  );

  const archiveCase = useCallback(async (caseId: string) => {
    const response = await fetch(`/api/cases/${caseId}/archive`, {
      method: "POST",
    });

    if (!response.ok) throw new Error("Archive failed");

    setCases((prev) => prev.filter((c) => c.id !== caseId));
    setTotalCount((prev) => prev - 1);
  }, []);

  const exportCases = useCallback(
    async (ids?: string[]) => {
      const params = new URLSearchParams();
      if (ids?.length) {
        params.set("ids", ids.join(","));
      } else {
        params.set("view", filters.view);
        if (filters.search) params.set("search", filters.search);
      }

      const response = await fetch(`/api/cases/export?${params}`);
      if (!response.ok) throw new Error("Export failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cases-export-${new Date().toISOString().split("T")[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    },
    [filters]
  );

  const hasMore = page < totalPages;

  return {
    cases,
    stats,
    facets,
    isLoading,
    isLoadingMore,
    error,
    page,
    totalPages,
    totalCount,
    hasMore,
    loadMore,
    filters,
    setFilters,
    resetFilters,
    sort,
    setSort,
    selectedIds,
    toggleSelect,
    selectAll,
    clearSelection,
    refreshCases: () => fetchCases(1, false),
    executeBulkAction,
    assignCase,
    updateCaseStatus,
    archiveCase,
    exportCases,
  };
}

// =============================================================================
// Real-time Updates Hook
// =============================================================================

interface UseRealtimeCasesOptions {
  onCaseEvent?: (event: CaseEvent) => void;
  onNotification?: (notification: CaseNotification) => void;
}

export function useRealtimeCases(options: UseRealtimeCasesOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<CaseNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/ws/cases`;

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      console.log("WebSocket connected");
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "case_event") {
          options.onCaseEvent?.(data.payload as CaseEvent);
        } else if (data.type === "notification") {
          const notification = data.payload as CaseNotification;
          setNotifications((prev) => [notification, ...prev.slice(0, 49)]);
          setUnreadCount((prev) => prev + 1);
          options.onNotification?.(notification);
        }
      } catch (e) {
        console.error("WebSocket message parse error:", e);
      }
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    wsRef.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }, [options]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  const markAsRead = useCallback((notificationId: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnreadCount(0);
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  return {
    isConnected,
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  };
}

// =============================================================================
// Virtual Scrolling Hook
// =============================================================================

interface UseVirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

export function useVirtualScroll<T>(
  items: T[],
  options: UseVirtualScrollOptions
) {
  const { itemHeight, containerHeight, overscan = 5 } = options;
  const [scrollTop, setScrollTop] = useState(0);

  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / itemHeight),
    items.length
  );

  const startIndex = Math.max(0, visibleStart - overscan);
  const endIndex = Math.min(items.length, visibleEnd + overscan);

  const visibleItems = useMemo(
    () =>
      items.slice(startIndex, endIndex).map((item, index) => ({
        item,
        index: startIndex + index,
        style: {
          position: "absolute" as const,
          top: (startIndex + index) * itemHeight,
          height: itemHeight,
          width: "100%",
        },
      })),
    [items, startIndex, endIndex, itemHeight]
  );

  const totalHeight = items.length * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    handleScroll,
    startIndex,
    endIndex,
  };
}
