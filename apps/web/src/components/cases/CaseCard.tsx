/**
 * NEURAXIS - Case Card Component
 * Card component for displaying case summary with hover actions
 */

"use client";

import { cn, formatRelativeTime, getInitials } from "@/lib/utils";
import type { CaseStatus, CaseSummary } from "@/types/case-dashboard";
import { PRIORITY_CONFIG, STATUS_CONFIG } from "@/types/case-dashboard";
import React, { memo, useState } from "react";

interface CaseCardProps {
  caseData: CaseSummary;
  isSelected?: boolean;
  onSelect?: () => void;
  onOpen?: () => void;
  onAssign?: () => void;
  onArchive?: () => void;
  onStatusChange?: (status: CaseStatus) => void;
  isDragging?: boolean;
}

export const CaseCard = memo(function CaseCard({
  caseData,
  isSelected = false,
  onSelect,
  onOpen,
  onAssign,
  onArchive,
  onStatusChange,
  isDragging = false,
}: CaseCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const priorityConfig = PRIORITY_CONFIG[caseData.priority];
  const statusConfig = STATUS_CONFIG[caseData.status];

  return (
    <div
      className={cn(
        "group relative rounded-xl border bg-card p-4 transition-all duration-200",
        "hover:shadow-lg hover:border-primary/30",
        isSelected && "ring-2 ring-primary border-primary",
        isDragging && "opacity-50 scale-95 rotate-2",
        caseData.isUnread && "border-l-4 border-l-primary"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onOpen}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onOpen?.()}
    >
      {/* Selection checkbox */}
      <div
        className={cn(
          "absolute top-3 left-3 z-10 transition-opacity",
          isHovered || isSelected ? "opacity-100" : "opacity-0"
        )}
        onClick={(e) => {
          e.stopPropagation();
          onSelect?.();
        }}
      >
        <div
          className={cn(
            "h-5 w-5 rounded border-2 flex items-center justify-center transition-colors cursor-pointer",
            isSelected
              ? "bg-primary border-primary text-primary-foreground"
              : "border-muted-foreground/50 hover:border-primary"
          )}
        >
          {isSelected && (
            <svg
              className="h-3 w-3"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
        </div>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          {/* Priority indicator */}
          <div
            className={cn(
              "h-2 w-2 rounded-full shrink-0",
              caseData.priority === "critical" && "bg-danger animate-pulse",
              caseData.priority === "high" && "bg-orange-500",
              caseData.priority === "moderate" && "bg-warning",
              caseData.priority === "low" && "bg-success"
            )}
          />

          <span className="text-sm font-medium text-muted-foreground">
            {caseData.caseNumber}
          </span>
        </div>

        {/* Priority & Status badges */}
        <div className="flex items-center gap-2 shrink-0">
          <span
            className={cn(
              "px-2 py-0.5 rounded-full text-xs font-medium",
              priorityConfig.bgColor,
              priorityConfig.color
            )}
          >
            {priorityConfig.label}
          </span>
          <span
            className={cn(
              "px-2 py-0.5 rounded-full text-xs font-medium",
              statusConfig.bgColor,
              statusConfig.color
            )}
          >
            {statusConfig.label}
          </span>
        </div>
      </div>

      {/* Patient info */}
      <div className="flex items-center gap-3 mb-3">
        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
          {caseData.patient.avatarUrl ? (
            <img
              src={caseData.patient.avatarUrl}
              alt=""
              className="h-full w-full rounded-full object-cover"
            />
          ) : (
            <span className="text-sm font-bold text-primary">
              {getInitials(caseData.patient.fullName)}
            </span>
          )}
        </div>
        <div className="min-w-0">
          <h3 className="font-semibold truncate">
            {caseData.patient.fullName}
          </h3>
          <p className="text-sm text-muted-foreground">
            {caseData.patient.age}y {caseData.patient.gender} • MRN:{" "}
            {caseData.patient.mrn}
          </p>
        </div>
      </div>

      {/* Chief complaint */}
      <div className="mb-3">
        <p className="text-sm font-medium line-clamp-2">
          {caseData.chiefComplaint}
        </p>
        {caseData.primaryDiagnosis && (
          <p className="text-sm text-muted-foreground mt-1">
            Dx: {caseData.primaryDiagnosis}
          </p>
        )}
      </div>

      {/* Meta info */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-3">
          {caseData.symptomsCount > 0 && (
            <span className="flex items-center gap-1">
              <svg
                className="h-3.5 w-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
              {caseData.symptomsCount}
            </span>
          )}
          {caseData.imagesCount > 0 && (
            <span className="flex items-center gap-1">
              <svg
                className="h-3.5 w-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
              {caseData.imagesCount}
            </span>
          )}
          {caseData.hasAISuggestions && (
            <span className="flex items-center gap-1 text-primary">
              <svg
                className="h-3.5 w-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a2 2 0 0 1 0 4h-1v1a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-1H6a2 2 0 0 1 0-4h1V7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
              </svg>
              AI
            </span>
          )}
        </div>
        <span>{formatRelativeTime(caseData.updatedAt)}</span>
      </div>

      {/* Assigned doctor */}
      <div className="mt-3 pt-3 border-t flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded-full bg-muted flex items-center justify-center text-xs font-medium">
            {getInitials(caseData.assignedTo.name)}
          </div>
          <span className="text-xs text-muted-foreground">
            Dr. {caseData.assignedTo.name.split(" ").pop()}
          </span>
        </div>

        {caseData.lastActivity && (
          <span className="text-xs text-muted-foreground">
            {caseData.lastActivity.action}
          </span>
        )}
      </div>

      {/* Hover actions */}
      <div
        className={cn(
          "absolute top-3 right-3 flex items-center gap-1 transition-opacity",
          isHovered ? "opacity-100" : "opacity-0"
        )}
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
            onOpen?.();
          }}
          className="p-1.5 rounded-lg bg-background/80 backdrop-blur border hover:bg-muted transition-colors"
          title="Open case"
        >
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
          </svg>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onAssign?.();
          }}
          className="p-1.5 rounded-lg bg-background/80 backdrop-blur border hover:bg-muted transition-colors"
          title="Assign case"
        >
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
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onArchive?.();
          }}
          className="p-1.5 rounded-lg bg-background/80 backdrop-blur border hover:bg-muted transition-colors"
          title="Archive case"
        >
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="21 8 21 21 3 21 3 8" />
            <rect x="1" y="3" width="22" height="5" />
            <line x1="10" y1="12" x2="14" y2="12" />
          </svg>
        </button>
      </div>
    </div>
  );
});

// =============================================================================
// Compact Case Card for List View
// =============================================================================

interface CompactCaseCardProps {
  caseData: CaseSummary;
  isSelected?: boolean;
  onSelect?: () => void;
  onOpen?: () => void;
  style?: React.CSSProperties;
}

export const CompactCaseCard = memo(function CompactCaseCard({
  caseData,
  isSelected = false,
  onSelect,
  onOpen,
  style,
}: CompactCaseCardProps) {
  const priorityConfig = PRIORITY_CONFIG[caseData.priority];
  const statusConfig = STATUS_CONFIG[caseData.status];

  return (
    <div
      className={cn(
        "flex items-center gap-4 px-4 py-3 border-b hover:bg-muted/50 transition-colors cursor-pointer",
        isSelected && "bg-primary/5",
        caseData.isUnread && "bg-primary/5"
      )}
      style={style}
      onClick={onOpen}
    >
      {/* Checkbox */}
      <div
        onClick={(e) => {
          e.stopPropagation();
          onSelect?.();
        }}
        className={cn(
          "h-4 w-4 rounded border-2 flex items-center justify-center shrink-0 cursor-pointer",
          isSelected
            ? "bg-primary border-primary text-primary-foreground"
            : "border-muted-foreground/50 hover:border-primary"
        )}
      >
        {isSelected && (
          <svg
            className="h-2.5 w-2.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )}
      </div>

      {/* Priority dot */}
      <div
        className={cn(
          "h-2 w-2 rounded-full shrink-0",
          caseData.priority === "critical" && "bg-danger animate-pulse",
          caseData.priority === "high" && "bg-orange-500",
          caseData.priority === "moderate" && "bg-warning",
          caseData.priority === "low" && "bg-success"
        )}
      />

      {/* Case number */}
      <span className="text-sm text-muted-foreground w-28 shrink-0">
        {caseData.caseNumber}
      </span>

      {/* Patient */}
      <div className="flex items-center gap-2 w-48 shrink-0">
        <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
          <span className="text-xs font-bold text-primary">
            {getInitials(caseData.patient.fullName)}
          </span>
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">
            {caseData.patient.fullName}
          </p>
          <p className="text-xs text-muted-foreground">
            MRN: {caseData.patient.mrn}
          </p>
        </div>
      </div>

      {/* Chief complaint */}
      <div className="flex-1 min-w-0">
        <p className="text-sm truncate">{caseData.chiefComplaint}</p>
      </div>

      {/* Status */}
      <span
        className={cn(
          "px-2 py-0.5 rounded-full text-xs font-medium w-24 text-center shrink-0",
          statusConfig.bgColor,
          statusConfig.color
        )}
      >
        {statusConfig.label}
      </span>

      {/* Assigned */}
      <div className="w-28 shrink-0 text-sm text-muted-foreground truncate">
        Dr. {caseData.assignedTo.name.split(" ").pop()}
      </div>

      {/* Updated */}
      <span className="text-xs text-muted-foreground w-20 shrink-0 text-right">
        {formatRelativeTime(caseData.updatedAt)}
      </span>
    </div>
  );
});

export default CaseCard;
