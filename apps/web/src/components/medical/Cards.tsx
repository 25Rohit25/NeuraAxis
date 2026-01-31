/**
 * NEURAXIS - Medical Card Components
 * PatientCard, CaseCard, DiagnosisCard, TimelineCard
 */

import { cn } from "@/lib/utils";
import React from "react";

// ============================================================================
// PATIENT CARD
// ============================================================================

export interface PatientCardProps {
  id: string;
  firstName: string;
  lastName: string;
  mrn: string; // Medical Record Number
  dateOfBirth: string;
  gender: "male" | "female" | "other";
  status: "active" | "discharged" | "critical" | "stable";
  lastVisit?: string;
  primaryDiagnosis?: string;
  avatarUrl?: string;
  onClick?: () => void;
  className?: string;
}

const statusStyles = {
  active: "bg-success/10 text-success",
  discharged: "bg-secondary/20 text-secondary-foreground",
  critical: "bg-danger/10 text-danger",
  stable: "bg-primary/10 text-primary",
};

export function PatientCard({
  id,
  firstName,
  lastName,
  mrn,
  dateOfBirth,
  gender,
  status,
  lastVisit,
  primaryDiagnosis,
  avatarUrl,
  onClick,
  className,
}: PatientCardProps) {
  const initials = `${firstName[0]}${lastName[0]}`.toUpperCase();
  const age = new Date().getFullYear() - new Date(dateOfBirth).getFullYear();

  const Card = onClick ? "button" : "div";

  return (
    <Card
      onClick={onClick}
      className={cn(
        "w-full text-left p-4 rounded-lg border bg-card shadow-card transition-all duration-200",
        onClick &&
          "hover:shadow-card-hover hover:border-primary/30 cursor-pointer",
        className
      )}
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="shrink-0">
          {avatarUrl ? (
            <img
              src={avatarUrl}
              alt={`${firstName} ${lastName}`}
              className="h-12 w-12 rounded-full object-cover"
            />
          ) : (
            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-medium">
              {initials}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold truncate">
              {firstName} {lastName}
            </h3>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-xs font-medium",
                statusStyles[status]
              )}
            >
              {status}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            MRN: {mrn} • {age}y{" "}
            {gender === "male" ? "M" : gender === "female" ? "F" : "O"}
          </p>
          {primaryDiagnosis && (
            <p className="text-sm text-muted-foreground mt-1 truncate">
              <span className="font-medium">Dx:</span> {primaryDiagnosis}
            </p>
          )}
        </div>

        {/* Last visit */}
        {lastVisit && (
          <div className="hidden sm:block text-right text-sm text-muted-foreground shrink-0">
            <p className="text-xs">Last Visit</p>
            <p className="font-medium">{lastVisit}</p>
          </div>
        )}
      </div>
    </Card>
  );
}

// ============================================================================
// CASE CARD
// ============================================================================

export interface CaseCardProps {
  id: string;
  patientName: string;
  caseNumber: string;
  status: "open" | "in_progress" | "pending_review" | "closed";
  priority: "low" | "medium" | "high" | "urgent";
  chiefComplaint: string;
  createdAt: string;
  assignedTo?: string;
  onClick?: () => void;
  className?: string;
}

const caseStatusStyles = {
  open: "bg-primary/10 text-primary",
  in_progress: "bg-warning/10 text-warning",
  pending_review: "bg-accent/10 text-accent",
  closed: "bg-secondary/20 text-secondary-foreground",
};

const priorityStyles = {
  low: "border-l-success",
  medium: "border-l-warning",
  high: "border-l-orange-500",
  urgent: "border-l-danger",
};

export function CaseCard({
  id,
  patientName,
  caseNumber,
  status,
  priority,
  chiefComplaint,
  createdAt,
  assignedTo,
  onClick,
  className,
}: CaseCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "p-4 rounded-lg border-l-4 bg-card shadow-card transition-all duration-200",
        priorityStyles[priority],
        onClick && "hover:shadow-card-hover cursor-pointer",
        className
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-muted-foreground">
              #{caseNumber}
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-xs font-medium",
                caseStatusStyles[status]
              )}
            >
              {status.replace("_", " ")}
            </span>
          </div>
          <h3 className="font-semibold mt-1">{patientName}</h3>
          <p className="text-sm text-muted-foreground mt-1 truncate-2">
            {chiefComplaint}
          </p>
        </div>

        {/* Priority indicator */}
        <div className="shrink-0 text-right">
          <span
            className={cn(
              "inline-flex items-center gap-1 text-xs font-medium",
              priority === "urgent" && "text-danger",
              priority === "high" && "text-orange-500",
              priority === "medium" && "text-warning",
              priority === "low" && "text-success"
            )}
          >
            {priority === "urgent" && (
              <svg
                className="w-3 h-3 animate-pulse"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <circle cx="12" cy="12" r="10" />
              </svg>
            )}
            {priority.toUpperCase()}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between mt-3 pt-3 border-t text-xs text-muted-foreground">
        <span>{createdAt}</span>
        {assignedTo && <span>Assigned: {assignedTo}</span>}
      </div>
    </div>
  );
}

// ============================================================================
// DIAGNOSIS CARD
// ============================================================================

export interface DiagnosisCardProps {
  id: string;
  condition: string;
  icdCode?: string;
  confidence: number; // 0-100
  severity: "minimal" | "mild" | "moderate" | "severe" | "critical";
  differentials?: string[];
  aiGenerated?: boolean;
  verifiedBy?: string;
  createdAt: string;
  onClick?: () => void;
  className?: string;
}

const severityStyles = {
  minimal: "bg-success/10 text-success border-success/30",
  mild: "bg-lime-100 text-lime-700 dark:bg-lime-900/20 dark:text-lime-400 border-lime-300",
  moderate: "bg-warning/10 text-warning border-warning/30",
  severe:
    "bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400 border-orange-300",
  critical: "bg-danger/10 text-danger border-danger/30",
};

export function DiagnosisCard({
  id,
  condition,
  icdCode,
  confidence,
  severity,
  differentials,
  aiGenerated,
  verifiedBy,
  createdAt,
  onClick,
  className,
}: DiagnosisCardProps) {
  const confidenceColor =
    confidence >= 80
      ? "text-success"
      : confidence >= 60
        ? "text-warning"
        : "text-danger";

  return (
    <div
      onClick={onClick}
      className={cn(
        "p-4 rounded-lg border bg-card shadow-card transition-all duration-200",
        onClick && "hover:shadow-card-hover cursor-pointer",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            {aiGenerated && (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-accent">
                <svg
                  className="w-3 h-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
                  <path d="M9 15v2M15 15v2" />
                </svg>
                AI Generated
              </span>
            )}
            {icdCode && (
              <span className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded">
                {icdCode}
              </span>
            )}
          </div>
          <h3 className="font-semibold mt-1">{condition}</h3>
        </div>

        {/* Severity badge */}
        <span
          className={cn(
            "rounded-full px-2.5 py-1 text-xs font-medium border",
            severityStyles[severity]
          )}
        >
          {severity}
        </span>
      </div>

      {/* Confidence meter */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-muted-foreground">Confidence</span>
          <span className={cn("font-semibold", confidenceColor)}>
            {confidence}%
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              confidence >= 80 && "bg-success",
              confidence >= 60 && confidence < 80 && "bg-warning",
              confidence < 60 && "bg-danger"
            )}
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>

      {/* Differentials */}
      {differentials && differentials.length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-xs text-muted-foreground mb-2">
            Differential Diagnoses
          </p>
          <div className="flex flex-wrap gap-1">
            {differentials.slice(0, 3).map((diff, index) => (
              <span
                key={index}
                className="text-xs bg-muted px-2 py-0.5 rounded"
              >
                {diff}
              </span>
            ))}
            {differentials.length > 3 && (
              <span className="text-xs text-muted-foreground">
                +{differentials.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t text-xs text-muted-foreground">
        <span>{createdAt}</span>
        {verifiedBy && (
          <span className="flex items-center gap-1">
            <svg
              className="w-3 h-3 text-success"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            Verified by {verifiedBy}
          </span>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// TIMELINE CARD
// ============================================================================

export interface TimelineEvent {
  id: string;
  type:
    | "visit"
    | "diagnosis"
    | "treatment"
    | "lab"
    | "imaging"
    | "note"
    | "medication";
  title: string;
  description?: string;
  date: string;
  provider?: string;
}

export interface TimelineCardProps {
  events: TimelineEvent[];
  className?: string;
}

const eventTypeStyles: Record<
  TimelineEvent["type"],
  { bg: string; icon: React.ReactNode }
> = {
  visit: {
    bg: "bg-primary",
    icon: (
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  diagnosis: {
    bg: "bg-accent",
    icon: (
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
  },
  treatment: {
    bg: "bg-success",
    icon: (
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
        <path d="m16 2-2.3 2.3a3 3 0 0 0 0 4.2l1.8 1.8a3 3 0 0 0 4.2 0L22 8" />
        <path d="M15 15 3.3 3.3a4.2 4.2 0 0 0 0 6l7.3 7.3c1.7 1.7 4.3 1.7 6 0L15 15z" />
      </svg>
    ),
  },
  lab: {
    bg: "bg-purple-500",
    icon: (
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
        <path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2" />
        <path d="M8.5 2h7" />
      </svg>
    ),
  },
  imaging: {
    bg: "bg-indigo-500",
    icon: (
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="9" cy="9" r="2" />
      </svg>
    ),
  },
  note: {
    bg: "bg-secondary-400",
    icon: (
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    ),
  },
  medication: {
    bg: "bg-pink-500",
    icon: (
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
        <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
        <path d="m8.5 8.5 7 7" />
      </svg>
    ),
  },
};

export function TimelineCard({ events, className }: TimelineCardProps) {
  return (
    <div className={cn("p-4 rounded-lg border bg-card", className)}>
      <h3 className="font-semibold mb-4">Patient Timeline</h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-3 top-0 bottom-0 w-px bg-border" />

        {/* Events */}
        <div className="space-y-4">
          {events.map((event, index) => {
            const style = eventTypeStyles[event.type];
            return (
              <div key={event.id} className="relative pl-8">
                {/* Event dot */}
                <div
                  className={cn(
                    "absolute left-0 w-6 h-6 rounded-full flex items-center justify-center text-white",
                    style.bg
                  )}
                >
                  {style.icon}
                </div>

                {/* Event content */}
                <div className="pb-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-sm">{event.title}</h4>
                    <span className="text-xs text-muted-foreground">
                      {event.date}
                    </span>
                  </div>
                  {event.description && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {event.description}
                    </p>
                  )}
                  {event.provider && (
                    <p className="text-xs text-muted-foreground mt-1">
                      by {event.provider}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
