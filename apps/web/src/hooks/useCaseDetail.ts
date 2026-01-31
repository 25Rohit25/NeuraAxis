/**
 * NEURAXIS - Case Detail Hooks
 * React hooks for case detail view and real-time collaboration
 */

"use client";

import type {
  AddCommentRequest,
  CaseDetail,
  CommentThread,
  ExportOptions,
  Presence,
  TimelineEvent,
  UpdateCaseRequest,
  VersionHistoryEntry,
} from "@/types/case-detail";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

// =============================================================================
// Case Detail Hook
// =============================================================================

interface UseCaseDetailOptions {
  caseId: string;
  enableRealtime?: boolean;
  autoRefreshInterval?: number;
}

interface UseCaseDetailReturn {
  // Data
  caseData: CaseDetail | null;
  timeline: TimelineEvent[];
  comments: CommentThread[];
  versionHistory: VersionHistoryEntry[];

  // Loading states
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;

  // Actions
  updateSection: (section: string, data: any) => Promise<void>;
  addComment: (request: AddCommentRequest) => Promise<void>;
  resolveThread: (threadId: string) => Promise<void>;
  exportCase: (options: ExportOptions) => Promise<string>;
  refreshCase: () => Promise<void>;

  // Timeline
  loadMoreTimeline: () => Promise<void>;
  hasMoreTimeline: boolean;

  // Version control
  revertToVersion: (versionId: string) => Promise<void>;
  compareVersions: (v1: string, v2: string) => Promise<any>;

  // Lock management
  acquireLock: (section?: string) => Promise<boolean>;
  releaseLock: () => Promise<void>;
  isLocked: boolean;
  lockedBy: string | null;
}

export function useCaseDetail(
  options: UseCaseDetailOptions
): UseCaseDetailReturn {
  const {
    caseId,
    enableRealtime = true,
    autoRefreshInterval = 30000,
  } = options;

  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [comments, setComments] = useState<CommentThread[]>([]);
  const [versionHistory, setVersionHistory] = useState<VersionHistoryEntry[]>(
    []
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timelinePage, setTimelinePage] = useState(1);
  const [hasMoreTimeline, setHasMoreTimeline] = useState(true);
  const [isLocked, setIsLocked] = useState(false);
  const [lockedBy, setLockedBy] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const currentVersionRef = useRef<number>(0);

  // Fetch case data
  const fetchCase = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/cases/${caseId}`, {
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) throw new Error("Failed to load case");

      const data = await response.json();
      setCaseData(data);
      setTimeline(data.timeline || []);
      setComments(data.comments || []);
      currentVersionRef.current = data.version;
      setIsLocked(data.isLocked || false);
      setLockedBy(data.lockedBy?.fullName || null);
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    fetchCase();
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [fetchCase]);

  // Update section with optimistic locking
  const updateSection = useCallback(
    async (section: string, data: any) => {
      setIsSaving(true);
      setError(null);

      try {
        const request: UpdateCaseRequest = {
          section,
          data,
          version: currentVersionRef.current,
        };

        const response = await fetch(`/api/cases/${caseId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          const error = await response.json();
          if (response.status === 409) {
            throw new Error(
              "Conflict: Case was modified by another user. Please refresh."
            );
          }
          throw new Error(error.detail || "Failed to update");
        }

        const updatedCase = await response.json();
        setCaseData(updatedCase);
        currentVersionRef.current = updatedCase.version;
      } catch (err: any) {
        setError(err.message);
        throw err;
      } finally {
        setIsSaving(false);
      }
    },
    [caseId]
  );

  // Add comment
  const addComment = useCallback(
    async (request: AddCommentRequest) => {
      const response = await fetch(`/api/cases/${caseId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });

      if (!response.ok) throw new Error("Failed to add comment");

      const newComment = await response.json();

      setComments((prev) => {
        const threadIndex = prev.findIndex(
          (t) => t.sectionId === request.sectionId
        );
        if (threadIndex >= 0) {
          const updated = [...prev];
          updated[threadIndex] = {
            ...updated[threadIndex],
            comments: [...updated[threadIndex].comments, newComment],
          };
          return updated;
        } else {
          return [
            ...prev,
            {
              id: newComment.threadId,
              sectionId: request.sectionId,
              sectionType: request.sectionType as any,
              comments: [newComment],
              isResolved: false,
              createdAt: new Date().toISOString(),
            },
          ];
        }
      });
    },
    [caseId]
  );

  // Resolve thread
  const resolveThread = useCallback(
    async (threadId: string) => {
      const response = await fetch(
        `/api/cases/${caseId}/comments/${threadId}/resolve`,
        {
          method: "POST",
        }
      );

      if (!response.ok) throw new Error("Failed to resolve thread");

      setComments((prev) =>
        prev.map((t) => (t.id === threadId ? { ...t, isResolved: true } : t))
      );
    },
    [caseId]
  );

  // Export case
  const exportCase = useCallback(
    async (options: ExportOptions): Promise<string> => {
      const response = await fetch(`/api/cases/${caseId}/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(options),
      });

      if (!response.ok) throw new Error("Export failed");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      // Trigger download
      const a = document.createElement("a");
      a.href = url;
      a.download = `case-${caseData?.caseNumber || caseId}.${options.format}`;
      a.click();

      return url;
    },
    [caseId, caseData?.caseNumber]
  );

  // Load more timeline
  const loadMoreTimeline = useCallback(async () => {
    const nextPage = timelinePage + 1;

    const response = await fetch(
      `/api/cases/${caseId}/timeline?page=${nextPage}&pageSize=20`
    );

    if (!response.ok) throw new Error("Failed to load timeline");

    const data = await response.json();

    setTimeline((prev) => [...prev, ...data.events]);
    setTimelinePage(nextPage);
    setHasMoreTimeline(data.hasMore);
  }, [caseId, timelinePage]);

  // Version history
  const fetchVersionHistory = useCallback(async () => {
    const response = await fetch(`/api/cases/${caseId}/versions`);
    if (response.ok) {
      const data = await response.json();
      setVersionHistory(data.versions);
    }
  }, [caseId]);

  const revertToVersion = useCallback(
    async (versionId: string) => {
      const response = await fetch(
        `/api/cases/${caseId}/versions/${versionId}/revert`,
        {
          method: "POST",
        }
      );

      if (!response.ok) throw new Error("Failed to revert");

      await fetchCase();
    },
    [caseId, fetchCase]
  );

  const compareVersions = useCallback(
    async (v1: string, v2: string) => {
      const response = await fetch(
        `/api/cases/${caseId}/versions/compare?v1=${v1}&v2=${v2}`
      );

      if (!response.ok) throw new Error("Failed to compare versions");

      return response.json();
    },
    [caseId]
  );

  // Lock management
  const acquireLock = useCallback(
    async (section?: string): Promise<boolean> => {
      const response = await fetch(`/api/cases/${caseId}/lock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section }),
      });

      if (response.status === 423) {
        const data = await response.json();
        setLockedBy(data.lockedBy);
        return false;
      }

      if (!response.ok) throw new Error("Failed to acquire lock");

      setIsLocked(true);
      return true;
    },
    [caseId]
  );

  const releaseLock = useCallback(async () => {
    await fetch(`/api/cases/${caseId}/lock`, {
      method: "DELETE",
    });
    setIsLocked(false);
    setLockedBy(null);
  }, [caseId]);

  return {
    caseData,
    timeline,
    comments,
    versionHistory,
    isLoading,
    isSaving,
    error,
    updateSection,
    addComment,
    resolveThread,
    exportCase,
    refreshCase: fetchCase,
    loadMoreTimeline,
    hasMoreTimeline,
    revertToVersion,
    compareVersions,
    acquireLock,
    releaseLock,
    isLocked,
    lockedBy,
  };
}

// =============================================================================
// Presence Hook
// =============================================================================

interface UsePresenceOptions {
  caseId: string;
  userId: string;
  userName: string;
}

export function usePresence(options: UsePresenceOptions) {
  const { caseId, userId, userName } = options;
  const [activeUsers, setActiveUsers] = useState<Presence[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout>();

  // Generate consistent color for user
  const userColor = useMemo(() => {
    const colors = [
      "#EF4444",
      "#F59E0B",
      "#10B981",
      "#3B82F6",
      "#8B5CF6",
      "#EC4899",
      "#06B6D4",
      "#84CC16",
    ];
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = (hash << 5) - hash + userId.charCodeAt(i);
    }
    return colors[Math.abs(hash) % colors.length];
  }, [userId]);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/ws/presence/${caseId}`;

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      // Send join message
      wsRef.current?.send(
        JSON.stringify({
          type: "join",
          userId,
          userName,
          color: userColor,
        })
      );

      // Start heartbeat
      heartbeatRef.current = setInterval(() => {
        wsRef.current?.send(JSON.stringify({ type: "heartbeat" }));
      }, 10000);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "presence_update") {
        setActiveUsers(data.users);
      } else if (data.type === "user_joined") {
        setActiveUsers((prev) => [
          ...prev.filter((u) => u.id !== data.user.id),
          data.user,
        ]);
      } else if (data.type === "user_left") {
        setActiveUsers((prev) => prev.filter((u) => u.id !== data.userId));
      } else if (data.type === "cursor_move") {
        setActiveUsers((prev) =>
          prev.map((u) =>
            u.id === data.userId
              ? { ...u, cursor: data.cursor, section: data.section }
              : u
          )
        );
      }
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      clearInterval(heartbeatRef.current);
    };

    return () => {
      clearInterval(heartbeatRef.current);
      wsRef.current?.close();
    };
  }, [caseId, userId, userName, userColor]);

  const updateCursor = useCallback(
    (cursor: { x: number; y: number }, section?: string) => {
      wsRef.current?.send(
        JSON.stringify({
          type: "cursor_move",
          cursor,
          section,
        })
      );
    },
    []
  );

  const updateSection = useCallback((section: string) => {
    wsRef.current?.send(
      JSON.stringify({
        type: "section_focus",
        section,
      })
    );
  }, []);

  return {
    activeUsers: activeUsers.filter((u) => u.id !== userId),
    isConnected,
    updateCursor,
    updateSection,
    userColor,
  };
}

// =============================================================================
// Collaborative Editor Hook (Y.js integration)
// =============================================================================

interface UseCollaborativeEditorOptions {
  caseId: string;
  noteId: string;
  userId: string;
}

export function useCollaborativeEditor(options: UseCollaborativeEditorOptions) {
  const { caseId, noteId, userId } = options;
  const [isSynced, setIsSynced] = useState(false);
  const [hasConflicts, setHasConflicts] = useState(false);
  const providerRef = useRef<any>(null);
  const docRef = useRef<any>(null);

  useEffect(() => {
    // This would integrate with Y.js and y-websocket
    // For now, return mock implementation

    const initCollaboration = async () => {
      try {
        // Dynamic import for Y.js (would be uncommented in real implementation)
        // const Y = await import('yjs');
        // const { WebsocketProvider } = await import('y-websocket');

        // docRef.current = new Y.Doc();
        // providerRef.current = new WebsocketProvider(
        //   `wss://${window.location.host}/api/ws/collab`,
        //   `case-${caseId}-note-${noteId}`,
        //   docRef.current
        // );

        setIsSynced(true);
      } catch (err) {
        console.error("Failed to initialize collaboration:", err);
      }
    };

    initCollaboration();

    return () => {
      providerRef.current?.destroy();
      docRef.current?.destroy();
    };
  }, [caseId, noteId]);

  return {
    isSynced,
    hasConflicts,
    document: docRef.current,
    provider: providerRef.current,
  };
}

// =============================================================================
// Timeline Infinite Scroll Hook
// =============================================================================

export function useInfiniteTimeline(caseId: string, pageSize: number = 20) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const observerRef = useRef<IntersectionObserver>();
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const loadPage = useCallback(
    async (pageNum: number) => {
      if (isLoading) return;

      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/cases/${caseId}/timeline?page=${pageNum}&pageSize=${pageSize}`
        );

        if (!response.ok) throw new Error("Failed to load timeline");

        const data = await response.json();

        setEvents((prev) =>
          pageNum === 1 ? data.events : [...prev, ...data.events]
        );
        setHasMore(data.hasMore);
        setPage(pageNum);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    },
    [caseId, pageSize, isLoading]
  );

  // Initial load
  useEffect(() => {
    loadPage(1);
  }, [caseId]);

  // Intersection observer for infinite scroll
  useEffect(() => {
    if (!loadMoreRef.current) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoading) {
          loadPage(page + 1);
        }
      },
      { threshold: 0.1 }
    );

    observerRef.current.observe(loadMoreRef.current);

    return () => observerRef.current?.disconnect();
  }, [hasMore, isLoading, page, loadPage]);

  return {
    events,
    isLoading,
    error,
    hasMore,
    loadMoreRef,
    refresh: () => loadPage(1),
  };
}
