/**
 * NEURAXIS - Medications List Component
 * Active medications with dosages, refill status, and actions
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { cn, formatDate } from "@/lib/utils";
import type { Medication, MedicationStatus } from "@/types/patient-profile";
import { useState } from "react";

interface MedicationsListProps {
  medications: Medication[];
  canEdit?: boolean;
  onAddMedication?: () => void;
  onEditMedication?: (medication: Medication) => void;
  onDiscontinue?: (medication: Medication) => void;
  isLoading?: boolean;
  className?: string;
}

const STATUS_STYLES: Record<
  MedicationStatus,
  { bg: string; text: string; label: string }
> = {
  active: { bg: "bg-success/10", text: "text-success", label: "Active" },
  on_hold: { bg: "bg-warning/10", text: "text-warning", label: "On Hold" },
  discontinued: {
    bg: "bg-muted",
    text: "text-muted-foreground",
    label: "Discontinued",
  },
  completed: { bg: "bg-info/10", text: "text-info", label: "Completed" },
};

export function MedicationsList({
  medications,
  canEdit = false,
  onAddMedication,
  onEditMedication,
  onDiscontinue,
  isLoading = false,
  className,
}: MedicationsListProps) {
  const [selectedMedication, setSelectedMedication] =
    useState<Medication | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [filter, setFilter] = useState<"all" | "active">("active");

  const filteredMedications = medications.filter((med) => {
    if (filter === "active")
      return med.status === "active" || med.status === "on_hold";
    return true;
  });

  const getRefillStatus = (med: Medication) => {
    if (!med.nextRefillDate) return null;
    const daysUntilRefill = Math.ceil(
      (new Date(med.nextRefillDate).getTime() - Date.now()) /
        (1000 * 60 * 60 * 24)
    );
    if (daysUntilRefill < 0) return { label: "Overdue", color: "text-danger" };
    if (daysUntilRefill <= 7)
      return { label: `${daysUntilRefill}d`, color: "text-warning" };
    return { label: `${daysUntilRefill}d`, color: "text-muted-foreground" };
  };

  if (isLoading) {
    return (
      <div className={cn("space-y-3", className)}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-4 rounded-lg border bg-card animate-pulse">
            <div className="h-4 w-1/3 bg-muted rounded mb-2" />
            <div className="h-3 w-2/3 bg-muted rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <button
            onClick={() => setFilter("active")}
            className={cn(
              "px-3 py-1 text-sm rounded-full transition-colors",
              filter === "active"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            Active (
            {
              medications.filter(
                (m) => m.status === "active" || m.status === "on_hold"
              ).length
            }
            )
          </button>
          <button
            onClick={() => setFilter("all")}
            className={cn(
              "px-3 py-1 text-sm rounded-full transition-colors",
              filter === "all"
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            All ({medications.length})
          </button>
        </div>
        {canEdit && onAddMedication && (
          <Button size="sm" onClick={onAddMedication}>
            Add Medication
          </Button>
        )}
      </div>

      {/* Medications list */}
      {filteredMedications.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground bg-muted/30 rounded-lg">
          <svg
            className="h-10 w-10 mx-auto mb-2 opacity-50"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
            <path d="m8.5 8.5 7 7" />
          </svg>
          <p>No medications found</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredMedications.map((med) => {
            const refillStatus = getRefillStatus(med);
            const statusStyle = STATUS_STYLES[med.status];

            return (
              <div
                key={med.id}
                onClick={() => {
                  setSelectedMedication(med);
                  setShowDetails(true);
                }}
                className="p-4 rounded-lg border bg-card hover:bg-muted/30 cursor-pointer transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {/* Name and status */}
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-sm truncate">
                        {med.name}
                      </h4>
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded-full text-xs font-medium",
                          statusStyle.bg,
                          statusStyle.text
                        )}
                      >
                        {statusStyle.label}
                      </span>
                      {med.isControlled && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-danger/10 text-danger">
                          Controlled
                        </span>
                      )}
                    </div>

                    {/* Dosage info */}
                    <p className="text-sm text-muted-foreground">
                      {med.dosage} • {med.frequency} • {med.route}
                    </p>

                    {/* Prescriber */}
                    <p className="text-xs text-muted-foreground mt-1">
                      Prescribed by {med.prescribedBy.name}
                    </p>
                  </div>

                  {/* Refill info */}
                  <div className="text-right shrink-0">
                    {med.status === "active" && refillStatus && (
                      <div className="mb-1">
                        <span className="text-xs text-muted-foreground">
                          Refill in{" "}
                        </span>
                        <span
                          className={cn(
                            "text-sm font-medium",
                            refillStatus.color
                          )}
                        >
                          {refillStatus.label}
                        </span>
                      </div>
                    )}
                    {med.refillsRemaining != null && (
                      <p className="text-xs text-muted-foreground">
                        {med.refillsRemaining} refills left
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Medication Details Modal */}
      <Modal
        isOpen={showDetails}
        onClose={() => setShowDetails(false)}
        title={selectedMedication?.name || ""}
        size="lg"
      >
        {selectedMedication && (
          <div className="space-y-6">
            {/* Basic info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">
                  Generic Name
                </p>
                <p className="text-sm font-medium">
                  {selectedMedication.genericName || "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Status</p>
                <span
                  className={cn(
                    "px-2 py-0.5 rounded-full text-xs font-medium",
                    STATUS_STYLES[selectedMedication.status].bg,
                    STATUS_STYLES[selectedMedication.status].text
                  )}
                >
                  {STATUS_STYLES[selectedMedication.status].label}
                </span>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Dosage</p>
                <p className="text-sm font-medium">
                  {selectedMedication.dosage}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Frequency</p>
                <p className="text-sm font-medium">
                  {selectedMedication.frequency}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Route</p>
                <p className="text-sm font-medium">
                  {selectedMedication.route}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Start Date</p>
                <p className="text-sm font-medium">
                  {formatDate(selectedMedication.startDate)}
                </p>
              </div>
            </div>

            {/* Instructions */}
            {selectedMedication.instructions && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">
                  Instructions
                </p>
                <p className="text-sm">{selectedMedication.instructions}</p>
              </div>
            )}

            {/* Side effects */}
            {selectedMedication.sideEffects &&
              selectedMedication.sideEffects.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">
                    Possible Side Effects
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedMedication.sideEffects.map((effect, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 rounded bg-muted text-xs"
                      >
                        {effect}
                      </span>
                    ))}
                  </div>
                </div>
              )}

            {/* Drug interactions */}
            {selectedMedication.interactions &&
              selectedMedication.interactions.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">
                    Drug Interactions
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedMedication.interactions.map((interaction, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 rounded bg-warning/10 text-warning text-xs"
                      >
                        {interaction}
                      </span>
                    ))}
                  </div>
                </div>
              )}

            {/* Actions */}
            {canEdit && selectedMedication.status === "active" && (
              <div className="flex gap-2 pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => {
                    onEditMedication?.(selectedMedication);
                    setShowDetails(false);
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  onClick={() => {
                    onDiscontinue?.(selectedMedication);
                    setShowDetails(false);
                  }}
                >
                  Discontinue
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

export default MedicationsList;
