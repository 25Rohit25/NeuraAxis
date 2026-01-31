/**
 * NEURAXIS - Case Detail Components
 * Reusable components for the case detail view
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import { cn, formatRelativeTime, getInitials } from "@/lib/utils";
import type {
  AddCommentRequest,
  AIAnalysisResult,
  CaseImageDetail,
  ClinicalNote,
  CommentThread,
  LabResultDetail,
  Presence,
  TimelineEvent,
  TreatmentPlan,
  VersionHistoryEntry,
} from "@/types/case-detail";
import React, { useEffect, useRef, useState } from "react";

// =============================================================================
// Presence Indicators
// =============================================================================

interface PresenceIndicatorsProps {
  users: Presence[];
  isConnected: boolean;
  maxDisplay?: number;
}

export function PresenceIndicators({
  users,
  isConnected,
  maxDisplay = 4,
}: PresenceIndicatorsProps) {
  const displayUsers = users.slice(0, maxDisplay);
  const remaining = users.length - maxDisplay;

  return (
    <div className="flex items-center gap-2">
      {/* Connection status */}
      <div
        className={cn(
          "h-2 w-2 rounded-full",
          isConnected ? "bg-success" : "bg-warning animate-pulse"
        )}
      />

      {/* User avatars */}
      <div className="flex -space-x-2">
        {displayUsers.map((user) => (
          <div
            key={user.id}
            className="relative h-8 w-8 rounded-full border-2 border-background flex items-center justify-center text-xs font-bold"
            style={{ backgroundColor: user.color + "20", color: user.color }}
            title={`${user.user.fullName}${user.section ? ` - viewing ${user.section}` : ""}`}
          >
            {getInitials(user.user.fullName)}
            {user.section && (
              <span
                className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full border border-background"
                style={{ backgroundColor: user.color }}
              />
            )}
          </div>
        ))}
        {remaining > 0 && (
          <div className="h-8 w-8 rounded-full border-2 border-background bg-muted flex items-center justify-center text-xs font-medium">
            +{remaining}
          </div>
        )}
      </div>

      {users.length > 0 && (
        <span className="text-xs text-muted-foreground">
          {users.length} viewing
        </span>
      )}
    </div>
  );
}

// =============================================================================
// Timeline Component
// =============================================================================

interface CaseTimelineProps {
  caseId: string;
  initialEvents: TimelineEvent[];
}

const EVENT_ICONS: Record<string, React.ReactNode> = {
  case_created: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="12" y1="18" x2="12" y2="12" />
      <line x1="9" y1="15" x2="15" y2="15" />
    </svg>
  ),
  status_changed: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <polyline points="23 4 23 10 17 10" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  ),
  note_added: (
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
  assigned: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <line x1="19" y1="8" x2="19" y2="14" />
      <line x1="22" y1="11" x2="16" y2="11" />
    </svg>
  ),
  image_uploaded: (
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
  ai_analysis_run: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a2 2 0 0 1 0 4h-1v1a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-1H6a2 2 0 0 1 0-4h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
    </svg>
  ),
};

export function CaseTimeline({ caseId, initialEvents }: CaseTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>(initialEvents);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Infinite scroll
  useEffect(() => {
    if (!loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoading) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [hasMore, isLoading]);

  const loadMore = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/cases/${caseId}/timeline?page=${Math.ceil(events.length / 20) + 1}`
      );
      if (response.ok) {
        const data = await response.json();
        setEvents((prev) => [...prev, ...data.events]);
        setHasMore(data.hasMore);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-card rounded-xl border p-6">
      <h3 className="text-lg font-semibold mb-6">Activity Timeline</h3>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-5 top-0 bottom-0 w-px bg-border" />

        {/* Events */}
        <div className="space-y-6">
          {events.map((event, index) => (
            <div key={event.id} className="relative flex gap-4">
              {/* Icon */}
              <div
                className={cn(
                  "relative z-10 h-10 w-10 rounded-full flex items-center justify-center shrink-0",
                  event.type === "ai_analysis_run"
                    ? "bg-primary/10 text-primary"
                    : event.type.includes("error")
                      ? "bg-danger/10 text-danger"
                      : "bg-muted text-muted-foreground"
                )}
              >
                {EVENT_ICONS[event.type] || EVENT_ICONS.case_created}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 pb-4">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{event.title}</p>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatRelativeTime(event.timestamp)}
                  </span>
                </div>
                {event.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {event.description}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  by Dr. {event.actor?.lastName || "Unknown"}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Load more trigger */}
        <div ref={loadMoreRef} className="h-4" />

        {isLoading && (
          <div className="flex justify-center py-4">
            <svg
              className="h-6 w-6 animate-spin text-primary"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M21 12a9 9 0 11-6.219-8.56" />
            </svg>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Clinical Notes Editor
// =============================================================================

interface ClinicalNotesEditorProps {
  caseId: string;
  notes: ClinicalNote[];
  onUpdate: (data: any) => Promise<void>;
  presence: any;
}

export function ClinicalNotesEditor({
  caseId,
  notes,
  onUpdate,
  presence,
}: ClinicalNotesEditorProps) {
  const [activeNoteId, setActiveNoteId] = useState<string | null>(
    notes[0]?.id || null
  );
  const [isCreating, setIsCreating] = useState(false);
  const [content, setContent] = useState("");

  const activeNote = notes.find((n) => n.id === activeNoteId);

  const handleCreateNote = async () => {
    if (!content.trim()) return;

    await onUpdate({
      action: "create",
      data: {
        type: "progress",
        title: "Progress Note",
        content,
      },
    });

    setContent("");
    setIsCreating(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Notes list */}
      <div className="lg:col-span-1 bg-card rounded-xl border p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Notes</h3>
          <Button size="sm" onClick={() => setIsCreating(true)}>
            <svg
              className="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </Button>
        </div>

        <div className="space-y-2">
          {notes.map((note) => (
            <button
              key={note.id}
              onClick={() => setActiveNoteId(note.id)}
              className={cn(
                "w-full text-left p-3 rounded-lg transition-colors",
                activeNoteId === note.id ? "bg-primary/10" : "hover:bg-muted"
              )}
            >
              <p className="font-medium text-sm truncate">{note.title}</p>
              <p className="text-xs text-muted-foreground">
                {formatRelativeTime(note.updatedAt)}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Editor */}
      <div className="lg:col-span-3 bg-card rounded-xl border p-6">
        {isCreating ? (
          <div className="space-y-4">
            <h3 className="font-semibold">New Clinical Note</h3>
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter your clinical note..."
              rows={12}
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsCreating(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateNote}>Save Note</Button>
            </div>
          </div>
        ) : activeNote ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold">{activeNote.title}</h3>
                <p className="text-sm text-muted-foreground">
                  By Dr. {activeNote.author?.lastName} •{" "}
                  {formatRelativeTime(activeNote.updatedAt)}
                </p>
              </div>
              {activeNote.signedAt ? (
                <span className="px-3 py-1 rounded-full bg-success/10 text-success text-sm">
                  Signed
                </span>
              ) : (
                <Button size="sm">Sign Note</Button>
              )}
            </div>

            <div
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: activeNote.content }}
            />
          </div>
        ) : (
          <div className="text-center text-muted-foreground py-12">
            Select a note or create a new one
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// AI Analysis Panel
// =============================================================================

interface AIAnalysisPanelProps {
  analysis: AIAnalysisResult;
  onRerun: () => void;
}

export function AIAnalysisPanel({ analysis, onRerun }: AIAnalysisPanelProps) {
  const [expandedDx, setExpandedDx] = useState<number | null>(0);

  if (!analysis) {
    return (
      <div className="bg-card rounded-xl border p-6 text-center">
        <p className="text-muted-foreground">No AI analysis available</p>
        <Button className="mt-4" onClick={onRerun}>
          Run Analysis
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-br from-primary/5 to-primary/10 rounded-xl border border-primary/20 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <svg
                className="h-6 w-6 text-primary"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a2 2 0 0 1 0 4h-1v1a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-1H6a2 2 0 0 1 0-4h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold">AI Clinical Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Model: {analysis.modelVersion} •{" "}
                {formatRelativeTime(analysis.analyzedAt)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Confidence</p>
              <p className="text-2xl font-bold text-primary">
                {(analysis.confidence * 100).toFixed(0)}%
              </p>
            </div>
            <Button variant="outline" onClick={onRerun}>
              <svg
                className="h-4 w-4 mr-2"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              Re-run
            </Button>
          </div>
        </div>
      </div>

      {/* Urgency Assessment */}
      <div className="bg-card rounded-xl border p-6">
        <h4 className="font-semibold mb-4">Urgency Assessment</h4>
        <div
          className={cn(
            "inline-block px-4 py-2 rounded-lg font-semibold mb-4",
            analysis.urgencyAssessment.level === "critical" &&
              "bg-danger/10 text-danger",
            analysis.urgencyAssessment.level === "high" &&
              "bg-orange-500/10 text-orange-500",
            analysis.urgencyAssessment.level === "moderate" &&
              "bg-warning/10 text-warning",
            analysis.urgencyAssessment.level === "low" &&
              "bg-success/10 text-success"
          )}
        >
          {analysis.urgencyAssessment.level.toUpperCase()} Priority
        </div>
        <p className="text-sm mb-4">{analysis.urgencyAssessment.reasoning}</p>

        {analysis.urgencyAssessment.redFlags?.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-medium text-danger mb-2">⚠️ Red Flags</p>
            <ul className="list-disc list-inside text-sm space-y-1">
              {analysis.urgencyAssessment.redFlags.map((flag, i) => (
                <li key={i} className="text-danger">
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Differential Diagnosis */}
      <div className="bg-card rounded-xl border p-6">
        <h4 className="font-semibold mb-4">Differential Diagnosis</h4>
        <div className="space-y-3">
          {analysis.differentialDiagnosis.map((dx, index) => (
            <div
              key={index}
              className={cn(
                "border rounded-lg overflow-hidden transition-all",
                expandedDx === index && "ring-2 ring-primary"
              )}
            >
              <button
                onClick={() =>
                  setExpandedDx(expandedDx === index ? null : index)
                }
                className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold",
                      index === 0
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    )}
                  >
                    {index + 1}
                  </span>
                  <div className="text-left">
                    <p className="font-medium">{dx.diagnosis}</p>
                    {dx.icdCode && (
                      <p className="text-xs text-muted-foreground">
                        ICD-10: {dx.icdCode}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-32">
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${dx.probability * 100}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 text-right">
                      {(dx.probability * 100).toFixed(0)}%
                    </p>
                  </div>
                  <svg
                    className={cn(
                      "h-5 w-5 transition-transform",
                      expandedDx === index && "rotate-180"
                    )}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </div>
              </button>

              {expandedDx === index && (
                <div className="px-4 pb-4 border-t bg-muted/30">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                    <div>
                      <p className="text-sm font-medium mb-2">Reasoning</p>
                      <p className="text-sm text-muted-foreground">
                        {dx.reasoning}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium mb-2">
                        Supporting Evidence
                      </p>
                      <ul className="list-disc list-inside text-sm text-muted-foreground">
                        {dx.supportingEvidence.map((evidence, i) => (
                          <li key={i}>{evidence}</li>
                        ))}
                      </ul>
                    </div>
                    {dx.suggestedTests?.length > 0 && (
                      <div className="md:col-span-2">
                        <p className="text-sm font-medium mb-2">
                          Suggested Tests
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {dx.suggestedTests.map((test, i) => (
                            <span
                              key={i}
                              className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm"
                            >
                              {test}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-muted/50 rounded-xl p-4">
        <p className="text-xs text-muted-foreground">
          <strong>Disclaimer:</strong> {analysis.disclaimer}
        </p>
      </div>
    </div>
  );
}

// =============================================================================
// Treatment Plan Editor
// =============================================================================

interface TreatmentPlanEditorProps {
  plan: TreatmentPlan;
  onUpdate: (data: any) => Promise<void>;
}

export function TreatmentPlanEditor({
  plan,
  onUpdate,
}: TreatmentPlanEditorProps) {
  if (!plan) {
    return (
      <div className="bg-card rounded-xl border p-6 text-center">
        <p className="text-muted-foreground">No treatment plan yet</p>
        <Button className="mt-4">Create Treatment Plan</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Diagnosis */}
      <div className="bg-card rounded-xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold">Diagnosis</h4>
          <Button size="sm" variant="outline">
            Add Diagnosis
          </Button>
        </div>
        <div className="space-y-3">
          {plan.diagnosis?.map((dx) => (
            <div
              key={dx.id}
              className="flex items-center justify-between p-3 rounded-lg border"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-xs font-medium",
                      dx.type === "primary" && "bg-primary/10 text-primary",
                      dx.type === "secondary" &&
                        "bg-muted text-muted-foreground",
                      dx.type === "differential" && "bg-warning/10 text-warning"
                    )}
                  >
                    {dx.type}
                  </span>
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-xs",
                      dx.status === "confirmed" && "bg-success/10 text-success",
                      dx.status === "provisional" &&
                        "bg-warning/10 text-warning",
                      dx.status === "ruled-out" &&
                        "bg-muted text-muted-foreground line-through"
                    )}
                  >
                    {dx.status}
                  </span>
                </div>
                <p className="font-medium mt-1">{dx.description}</p>
                <p className="text-xs text-muted-foreground">
                  ICD-10: {dx.code}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Medications */}
      <div className="bg-card rounded-xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold">Prescribed Medications</h4>
          <Button size="sm" variant="outline">
            Add Medication
          </Button>
        </div>
        <div className="space-y-3">
          {plan.medications?.map((med) => (
            <div key={med.id} className="p-4 rounded-lg border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{med.medication}</p>
                  <p className="text-sm text-muted-foreground">
                    {med.dosage} • {med.frequency} • {med.route}
                  </p>
                </div>
                <p className="text-sm text-muted-foreground">{med.duration}</p>
              </div>
              {med.instructions && (
                <p className="text-sm mt-2 p-2 bg-muted rounded">
                  {med.instructions}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Follow-up */}
      {plan.followUp && (
        <div className="bg-card rounded-xl border p-6">
          <h4 className="font-semibold mb-4">Follow-up Plan</h4>
          <div className="grid grid-cols-2 gap-4">
            {plan.followUp.scheduledDate && (
              <div>
                <p className="text-sm text-muted-foreground">Scheduled Date</p>
                <p className="font-medium">{plan.followUp.scheduledDate}</p>
              </div>
            )}
            {plan.followUp.interval && (
              <div>
                <p className="text-sm text-muted-foreground">Interval</p>
                <p className="font-medium">{plan.followUp.interval}</p>
              </div>
            )}
            <div className="col-span-2">
              <p className="text-sm text-muted-foreground">Reason</p>
              <p className="font-medium">{plan.followUp.reason}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Image Gallery
// =============================================================================

interface ImageGalleryProps {
  images: CaseImageDetail[];
  caseId: string;
  onUpdate: (data: any) => Promise<void>;
}

export function ImageGallery({ images, caseId, onUpdate }: ImageGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<CaseImageDetail | null>(
    null
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">
          Medical Images ({images.length})
        </h3>
        <Button>Upload Image</Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {images.map((image) => (
          <div
            key={image.id}
            onClick={() => setSelectedImage(image)}
            className="group relative aspect-square rounded-xl overflow-hidden cursor-pointer border hover:shadow-lg transition-all"
          >
            <img
              src={image.thumbnailUrl || image.url}
              alt={image.description}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
              <div className="text-white">
                <p className="font-medium text-sm">{image.type}</p>
                {image.bodyPart && (
                  <p className="text-xs opacity-75">{image.bodyPart}</p>
                )}
              </div>
            </div>
            {image.aiAnnotations?.length > 0 && (
              <div className="absolute top-2 right-2 h-6 w-6 rounded-full bg-primary flex items-center justify-center">
                <svg
                  className="h-3 w-3 text-white"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a2 2 0 0 1 0 4h-1v1a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-1H6a2 2 0 0 1 0-4h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Lightbox modal would go here */}
    </div>
  );
}

// =============================================================================
// Lab Results Table
// =============================================================================

interface LabResultsTableProps {
  results: LabResultDetail[];
  onAddResult: () => void;
}

export function LabResultsTable({
  results,
  onAddResult,
}: LabResultsTableProps) {
  return (
    <div className="bg-card rounded-xl border overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold">Lab Results</h3>
        <Button size="sm" onClick={onAddResult}>
          Add Result
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Test</th>
              <th className="px-4 py-3 text-left text-sm font-medium">
                Result
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium">
                Normal Range
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium">
                Status
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium">Date</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result) => (
              <tr key={result.id} className="border-t hover:bg-muted/30">
                <td className="px-4 py-3">
                  <p className="font-medium">{result.testName}</p>
                  <p className="text-xs text-muted-foreground">
                    {result.category}
                  </p>
                </td>
                <td
                  className={cn(
                    "px-4 py-3 font-medium",
                    result.status === "normal" && "text-success",
                    result.status === "high" && "text-danger",
                    result.status === "low" && "text-warning",
                    result.status === "critical" && "text-danger font-bold"
                  )}
                >
                  {result.value} {result.unit}
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {result.normalRange.min} - {result.normalRange.max}{" "}
                  {result.unit}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      "px-2 py-1 rounded-full text-xs font-medium",
                      result.status === "normal" &&
                        "bg-success/10 text-success",
                      result.status === "high" && "bg-danger/10 text-danger",
                      result.status === "low" && "bg-warning/10 text-warning",
                      result.status === "critical" && "bg-danger text-white"
                    )}
                  >
                    {result.status === "critical" && "⚠️ "}
                    {result.status.charAt(0).toUpperCase() +
                      result.status.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3 text-muted-foreground text-sm">
                  {result.resultedAt
                    ? formatRelativeTime(result.resultedAt)
                    : "Pending"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// =============================================================================
// Comment Section
// =============================================================================

interface CommentSectionProps {
  caseId: string;
  threads: CommentThread[];
  onAddComment: (request: AddCommentRequest) => Promise<void>;
  onResolveThread: (threadId: string) => Promise<void>;
}

export function CommentSection({
  caseId,
  threads,
  onAddComment,
  onResolveThread,
}: CommentSectionProps) {
  const [newComment, setNewComment] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);

  const unresolved = threads.filter((t) => !t.isResolved);

  const handleSubmit = async () => {
    if (!newComment.trim()) return;

    await onAddComment({
      sectionId: "general",
      sectionType: "general",
      content: newComment,
    });

    setNewComment("");
  };

  return (
    <div
      className={cn(
        "fixed right-0 top-0 h-full bg-card border-l shadow-xl transition-all z-50",
        isExpanded ? "w-80" : "w-12"
      )}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 h-12 w-6 bg-card border rounded-l-lg flex items-center justify-center"
      >
        <svg
          className={cn(
            "h-4 w-4 transition-transform",
            isExpanded && "rotate-180"
          )}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>

      {isExpanded && (
        <div className="h-full flex flex-col">
          <div className="p-4 border-b">
            <h3 className="font-semibold">Comments</h3>
            {unresolved.length > 0 && (
              <p className="text-sm text-muted-foreground">
                {unresolved.length} unresolved
              </p>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {threads.map((thread) => (
              <div
                key={thread.id}
                className={cn(
                  "p-3 rounded-lg border",
                  thread.isResolved && "opacity-50"
                )}
              >
                {thread.comments.map((comment) => (
                  <div key={comment.id} className="mb-2 last:mb-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">
                        Dr. {comment.author.lastName}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatRelativeTime(comment.createdAt)}
                      </span>
                    </div>
                    <p className="text-sm">{comment.content}</p>
                  </div>
                ))}
                {!thread.isResolved && (
                  <button
                    onClick={() => onResolveThread(thread.id)}
                    className="text-xs text-primary hover:underline mt-2"
                  >
                    Resolve
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="p-4 border-t">
            <Textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              rows={2}
            />
            <Button
              className="w-full mt-2"
              size="sm"
              onClick={handleSubmit}
              disabled={!newComment.trim()}
            >
              Post Comment
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Version History Panel
// =============================================================================

interface VersionHistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  versions: VersionHistoryEntry[];
  onRevert: (versionId: string) => Promise<void>;
  onCompare: (v1: string, v2: string) => Promise<any>;
}

export function VersionHistoryPanel({
  isOpen,
  onClose,
  versions,
  onRevert,
  onCompare,
}: VersionHistoryPanelProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
      <div className="bg-card rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">Version History</h3>
          <button onClick={onClose} className="p-2 hover:bg-muted rounded-lg">
            <svg
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="overflow-y-auto max-h-[60vh] p-4">
          <div className="space-y-3">
            {versions.map((version, index) => (
              <div
                key={version.id}
                className="flex items-start gap-4 p-4 rounded-lg border hover:bg-muted/50"
              >
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span className="text-sm font-bold text-primary">
                    v{version.version}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">
                      {version.changeType === "create" ? "Created" : "Updated"}{" "}
                      {version.section}
                    </p>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(version.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    by Dr. {version.author.lastName}
                  </p>
                  {version.changes?.length > 0 && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {version.changes.length} change(s)
                    </p>
                  )}
                </div>
                {index > 0 && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onRevert(version.id)}
                  >
                    Restore
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Re-export for convenience
export { PresenceIndicators as CaseHeader };
