/**
 * NEURAXIS - Allergy & Conditions Components
 * Display and manage allergies and chronic conditions
 */

"use client";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import type {
  Allergy,
  AllergySeverity,
  ChronicCondition,
  ConditionStatus,
} from "@/types/patient-profile";
import React, { useState } from "react";

// =============================================================================
// Allergies List
// =============================================================================

interface AllergiesListProps {
  allergies: Allergy[];
  canEdit?: boolean;
  onAdd?: () => void;
  onEdit?: (allergy: Allergy) => void;
  isLoading?: boolean;
  className?: string;
}

const SEVERITY_STYLES: Record<
  AllergySeverity,
  { bg: string; text: string; border: string }
> = {
  mild: {
    bg: "bg-success/10",
    text: "text-success",
    border: "border-success/30",
  },
  moderate: {
    bg: "bg-warning/10",
    text: "text-warning",
    border: "border-warning/30",
  },
  severe: {
    bg: "bg-orange-500/10",
    text: "text-orange-500",
    border: "border-orange-500/30",
  },
  life_threatening: {
    bg: "bg-danger/10",
    text: "text-danger",
    border: "border-danger/30",
  },
};

const ALLERGY_TYPE_ICONS: Record<string, React.ReactNode> = {
  drug: (
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
  food: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
      <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
      <line x1="6" y1="1" x2="6" y2="4" />
      <line x1="10" y1="1" x2="10" y2="4" />
      <line x1="14" y1="1" x2="14" y2="4" />
    </svg>
  ),
  environmental: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  ),
  other: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
};

export function AllergiesList({
  allergies,
  canEdit = false,
  onAdd,
  onEdit,
  isLoading = false,
  className,
}: AllergiesListProps) {
  if (isLoading) {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="p-3 rounded-lg border animate-pulse">
            <div className="h-4 w-1/3 bg-muted rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <svg
            className="h-5 w-5 text-danger"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <h3 className="font-semibold text-sm">Allergies</h3>
          {allergies.length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs bg-danger/10 text-danger font-medium">
              {allergies.length}
            </span>
          )}
        </div>
        {canEdit && onAdd && (
          <Button size="xs" variant="outline" onClick={onAdd}>
            Add
          </Button>
        )}
      </div>

      {/* No allergies */}
      {allergies.length === 0 ? (
        <div className="p-4 rounded-lg bg-success/5 border border-success/20 text-center">
          <p className="text-sm text-success">No Known Allergies (NKA)</p>
        </div>
      ) : (
        <div className="space-y-2">
          {allergies.map((allergy) => {
            const severity = SEVERITY_STYLES[allergy.severity];
            return (
              <div
                key={allergy.id}
                onClick={() => canEdit && onEdit?.(allergy)}
                className={cn(
                  "p-3 rounded-lg border transition-colors",
                  severity.bg,
                  severity.border,
                  canEdit && "cursor-pointer hover:opacity-80"
                )}
              >
                <div className="flex items-start gap-3">
                  <span className={severity.text}>
                    {ALLERGY_TYPE_ICONS[allergy.type]}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">
                        {allergy.allergen}
                      </span>
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium uppercase",
                          severity.text
                        )}
                      >
                        {allergy.severity.replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Reaction: {allergy.reaction}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Conditions List
// =============================================================================

interface ConditionsListProps {
  conditions: ChronicCondition[];
  canEdit?: boolean;
  onAdd?: () => void;
  onEdit?: (condition: ChronicCondition) => void;
  isLoading?: boolean;
  className?: string;
}

const CONDITION_STATUS_STYLES: Record<
  ConditionStatus,
  { bg: string; text: string }
> = {
  active: { bg: "bg-warning/10", text: "text-warning" },
  chronic: { bg: "bg-orange-500/10", text: "text-orange-500" },
  in_remission: { bg: "bg-success/10", text: "text-success" },
  resolved: { bg: "bg-muted", text: "text-muted-foreground" },
};

export function ConditionsList({
  conditions,
  canEdit = false,
  onAdd,
  onEdit,
  isLoading = false,
  className,
}: ConditionsListProps) {
  const [showResolved, setShowResolved] = useState(false);

  const activeConditions = conditions.filter((c) => c.status !== "resolved");
  const resolvedConditions = conditions.filter((c) => c.status === "resolved");
  const displayConditions = showResolved ? conditions : activeConditions;

  if (isLoading) {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="p-3 rounded-lg border animate-pulse">
            <div className="h-4 w-1/2 bg-muted rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <svg
            className="h-5 w-5 text-warning"
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
          <h3 className="font-semibold text-sm">Chronic Conditions</h3>
          <span className="px-2 py-0.5 rounded-full text-xs bg-warning/10 text-warning font-medium">
            {activeConditions.length} active
          </span>
        </div>
        {canEdit && onAdd && (
          <Button size="xs" variant="outline" onClick={onAdd}>
            Add
          </Button>
        )}
      </div>

      {/* Conditions list */}
      {displayConditions.length === 0 ? (
        <div className="p-4 rounded-lg bg-muted/30 text-center">
          <p className="text-sm text-muted-foreground">
            No chronic conditions documented
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {displayConditions.map((condition) => {
            const statusStyle = CONDITION_STATUS_STYLES[condition.status];
            return (
              <div
                key={condition.id}
                onClick={() => canEdit && onEdit?.(condition)}
                className={cn(
                  "p-3 rounded-lg border bg-card transition-colors",
                  canEdit && "cursor-pointer hover:bg-muted/30"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">
                        {condition.name}
                      </span>
                      <span
                        className={cn(
                          "px-1.5 py-0.5 rounded text-xs font-medium capitalize",
                          statusStyle.bg,
                          statusStyle.text
                        )}
                      >
                        {condition.status.replace("_", " ")}
                      </span>
                    </div>
                    {condition.icdCode && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        ICD-10: {condition.icdCode}
                      </p>
                    )}
                    {condition.treatedBy && (
                      <p className="text-xs text-muted-foreground">
                        Treated by: {condition.treatedBy.name}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0">
                    Since {new Date(condition.diagnosisDate).getFullYear()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Show resolved toggle */}
      {resolvedConditions.length > 0 && (
        <button
          onClick={() => setShowResolved(!showResolved)}
          className="mt-3 text-xs text-muted-foreground hover:text-foreground"
        >
          {showResolved ? "Hide" : "Show"} {resolvedConditions.length} resolved
          condition{resolvedConditions.length > 1 ? "s" : ""}
        </button>
      )}
    </div>
  );
}

export { AllergiesList, ConditionsList };
