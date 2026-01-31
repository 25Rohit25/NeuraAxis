/**
 * NEURAXIS - Patient Timeline Component
 * Chronological medical events with filtering
 */

"use client";

import { cn, formatDate, formatTime } from "@/lib/utils";
import type { TimelineEvent, TimelineEventType } from "@/types/patient-profile";
import React, { useMemo, useState } from "react";

interface TimelineProps {
  events: TimelineEvent[];
  isLoading?: boolean;
  onEventClick?: (event: TimelineEvent) => void;
  className?: string;
}

const EVENT_ICONS: Record<TimelineEventType, React.ReactNode> = {
  visit: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  ),
  diagnosis: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  procedure: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  ),
  medication_start: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
      <path d="m8.5 8.5 7 7" />
    </svg>
  ),
  medication_end: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  ),
  lab_result: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M14.5 2v6a2 2 0 0 0 2 2h6" />
      <path d="M8.5 22h-5a2 2 0 0 1-2-2v-5" />
      <path d="M21.5 9v11a2 2 0 0 1-2 2h-11" />
      <path d="M3.5 14V4a2 2 0 0 1 2-2h9" />
    </svg>
  ),
  imaging: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  ),
  allergy_added: (
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
  note: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  ),
  document: (
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
};

const EVENT_COLORS: Record<TimelineEventType, string> = {
  visit: "bg-primary text-primary-foreground",
  diagnosis: "bg-warning text-warning-foreground",
  procedure: "bg-danger text-white",
  medication_start: "bg-success text-white",
  medication_end: "bg-muted text-muted-foreground",
  lab_result: "bg-info text-white",
  imaging: "bg-purple-500 text-white",
  allergy_added: "bg-orange-500 text-white",
  note: "bg-slate-500 text-white",
  document: "bg-cyan-500 text-white",
};

const EVENT_LABELS: Record<TimelineEventType, string> = {
  visit: "Visit",
  diagnosis: "Diagnosis",
  procedure: "Procedure",
  medication_start: "Medication Started",
  medication_end: "Medication Ended",
  lab_result: "Lab Result",
  imaging: "Imaging",
  allergy_added: "Allergy Added",
  note: "Note",
  document: "Document",
};

export function Timeline({
  events,
  isLoading,
  onEventClick,
  className,
}: TimelineProps) {
  const [selectedTypes, setSelectedTypes] = useState<TimelineEventType[]>([]);
  const [dateRange, setDateRange] = useState<
    "all" | "30days" | "90days" | "1year"
  >("all");

  // Filter events
  const filteredEvents = useMemo(() => {
    let filtered = [...events];

    // Filter by type
    if (selectedTypes.length > 0) {
      filtered = filtered.filter((e) => selectedTypes.includes(e.type));
    }

    // Filter by date range
    if (dateRange !== "all") {
      const now = new Date();
      const cutoff = new Date();
      if (dateRange === "30days") cutoff.setDate(now.getDate() - 30);
      if (dateRange === "90days") cutoff.setDate(now.getDate() - 90);
      if (dateRange === "1year") cutoff.setFullYear(now.getFullYear() - 1);

      filtered = filtered.filter((e) => new Date(e.date) >= cutoff);
    }

    // Sort by date descending
    return filtered.sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    );
  }, [events, selectedTypes, dateRange]);

  // Group events by date
  const groupedEvents = useMemo(() => {
    const groups: Record<string, TimelineEvent[]> = {};
    filteredEvents.forEach((event) => {
      const dateKey = event.date;
      if (!groups[dateKey]) groups[dateKey] = [];
      groups[dateKey].push(event);
    });
    return groups;
  }, [filteredEvents]);

  const toggleType = (type: TimelineEventType) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  if (isLoading) {
    return (
      <div className={cn("space-y-4", className)}>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4 animate-pulse">
            <div className="h-8 w-8 rounded-full bg-muted" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-1/3 bg-muted rounded" />
              <div className="h-3 w-2/3 bg-muted rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Filters */}
      <div className="mb-6 space-y-3">
        {/* Date range */}
        <div className="flex gap-2">
          {(["all", "30days", "90days", "1year"] as const).map((range) => (
            <button
              key={range}
              onClick={() => setDateRange(range)}
              className={cn(
                "px-3 py-1.5 text-xs rounded-full border transition-colors",
                dateRange === range
                  ? "bg-primary text-primary-foreground border-primary"
                  : "hover:bg-muted border-input"
              )}
            >
              {range === "all"
                ? "All Time"
                : range === "30days"
                  ? "30 Days"
                  : range === "90days"
                    ? "90 Days"
                    : "1 Year"}
            </button>
          ))}
        </div>

        {/* Type filters */}
        <div className="flex gap-1 flex-wrap">
          {(Object.keys(EVENT_LABELS) as TimelineEventType[]).map((type) => (
            <button
              key={type}
              onClick={() => toggleType(type)}
              className={cn(
                "px-2 py-1 text-xs rounded-full border transition-colors flex items-center gap-1",
                selectedTypes.includes(type)
                  ? `${EVENT_COLORS[type]} border-transparent`
                  : "hover:bg-muted border-input"
              )}
            >
              {EVENT_LABELS[type]}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline */}
      {Object.entries(groupedEvents).length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <p>No events found</p>
        </div>
      ) : (
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

          <div className="space-y-6">
            {Object.entries(groupedEvents).map(([date, dayEvents]) => (
              <div key={date}>
                {/* Date header */}
                <div className="relative flex items-center gap-4 mb-4">
                  <div className="h-8 w-8 rounded-full bg-background border-2 border-border flex items-center justify-center z-10">
                    <span className="text-xs font-medium">
                      {new Date(date).getDate()}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-muted-foreground">
                    {formatDate(date, {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                </div>

                {/* Events for this date */}
                <div className="ml-12 space-y-3">
                  {dayEvents.map((event) => (
                    <div
                      key={event.id}
                      onClick={() => onEventClick?.(event)}
                      className={cn(
                        "relative p-4 rounded-lg border bg-card transition-colors",
                        onEventClick && "cursor-pointer hover:bg-muted/50"
                      )}
                    >
                      {/* Icon */}
                      <div
                        className={cn(
                          "absolute -left-10 top-4 h-6 w-6 rounded-full flex items-center justify-center",
                          EVENT_COLORS[event.type]
                        )}
                      >
                        {EVENT_ICONS[event.type]}
                      </div>

                      {/* Content */}
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted">
                              {EVENT_LABELS[event.type]}
                            </span>
                            {event.time && (
                              <span className="text-xs text-muted-foreground">
                                {formatTime(event.time)}
                              </span>
                            )}
                          </div>
                          <h4 className="font-medium text-sm">{event.title}</h4>
                          {event.description && (
                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                              {event.description}
                            </p>
                          )}
                        </div>

                        {/* Provider */}
                        {event.provider && (
                          <div className="flex items-center gap-2 shrink-0">
                            <div className="h-6 w-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs">
                              {event.provider.name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </div>
                            <span className="text-xs text-muted-foreground hidden sm:block">
                              {event.provider.name}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Timeline;
