/**
 * NEURAXIS - Bulk Actions Toolbar
 * Toolbar for bulk operations on selected cases
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { cn } from "@/lib/utils";
import type {
  BulkAction,
  CaseDoctor,
  CasePriority,
  CaseStatus,
} from "@/types/case-dashboard";
import { PRIORITY_CONFIG, STATUS_CONFIG } from "@/types/case-dashboard";
import { useState } from "react";

interface BulkActionsToolbarProps {
  selectedCount: number;
  onClearSelection: () => void;
  onSelectAll: () => void;
  totalCount: number;
  onAction: (action: BulkAction, options?: any) => Promise<void>;
  availableDoctors?: CaseDoctor[];
}

export function BulkActionsToolbar({
  selectedCount,
  onClearSelection,
  onSelectAll,
  totalCount,
  onAction,
  availableDoctors = [],
}: BulkActionsToolbarProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeModal, setActiveModal] = useState<BulkAction | null>(null);
  const [selectedDoctor, setSelectedDoctor] = useState<string>("");
  const [selectedPriority, setSelectedPriority] =
    useState<CasePriority>("moderate");
  const [selectedStatus, setSelectedStatus] =
    useState<CaseStatus>("in_progress");

  const handleAction = async (action: BulkAction, options?: any) => {
    setIsProcessing(true);
    try {
      await onAction(action, options);
      setActiveModal(null);
    } catch (error) {
      console.error("Bulk action failed:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  if (selectedCount === 0) return null;

  return (
    <>
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 duration-200">
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-card border shadow-2xl">
          {/* Selection info */}
          <div className="flex items-center gap-2 pr-4 border-r">
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-sm font-bold text-primary">
                {selectedCount}
              </span>
            </div>
            <div className="text-sm">
              <span className="font-medium">{selectedCount} selected</span>
              {selectedCount < totalCount && (
                <button
                  onClick={onSelectAll}
                  className="ml-2 text-primary hover:underline"
                >
                  Select all {totalCount}
                </button>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setActiveModal("assign")}
              disabled={isProcessing}
            >
              <svg
                className="h-4 w-4 mr-1.5"
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
              Assign
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => setActiveModal("change_priority")}
              disabled={isProcessing}
            >
              <svg
                className="h-4 w-4 mr-1.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              Priority
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => setActiveModal("change_status")}
              disabled={isProcessing}
            >
              <svg
                className="h-4 w-4 mr-1.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              Status
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => handleAction("export")}
              disabled={isProcessing}
            >
              <svg
                className="h-4 w-4 mr-1.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              Export
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => handleAction("archive")}
              disabled={isProcessing}
            >
              <svg
                className="h-4 w-4 mr-1.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="21 8 21 21 3 21 3 8" />
                <rect x="1" y="3" width="22" height="5" />
                <line x1="10" y1="12" x2="14" y2="12" />
              </svg>
              Archive
            </Button>
          </div>

          {/* Clear selection */}
          <button
            onClick={onClearSelection}
            className="p-2 rounded-lg hover:bg-muted transition-colors"
            title="Clear selection"
          >
            <svg
              className="h-4 w-4"
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
      </div>

      {/* Assign Modal */}
      <Modal
        isOpen={activeModal === "assign"}
        onClose={() => setActiveModal(null)}
        title={`Assign ${selectedCount} case${selectedCount > 1 ? "s" : ""}`}
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Select a doctor to assign the selected cases to:
          </p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {availableDoctors.map((doctor) => (
              <label
                key={doctor.id}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors border",
                  selectedDoctor === doctor.id
                    ? "bg-primary/10 border-primary"
                    : "hover:bg-muted border-transparent"
                )}
              >
                <input
                  type="radio"
                  name="doctor"
                  value={doctor.id}
                  checked={selectedDoctor === doctor.id}
                  onChange={(e) => setSelectedDoctor(e.target.value)}
                  className="sr-only"
                />
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-bold text-primary">
                    {doctor.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .slice(0, 2)}
                  </span>
                </div>
                <div>
                  <p className="font-medium">Dr. {doctor.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {doctor.specialty}
                  </p>
                </div>
              </label>
            ))}
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setActiveModal(null)}>
              Cancel
            </Button>
            <Button
              onClick={() =>
                handleAction("assign", { doctorId: selectedDoctor })
              }
              disabled={!selectedDoctor || isProcessing}
              isLoading={isProcessing}
            >
              Assign Cases
            </Button>
          </div>
        </div>
      </Modal>

      {/* Change Priority Modal */}
      <Modal
        isOpen={activeModal === "change_priority"}
        onClose={() => setActiveModal(null)}
        title="Change Priority"
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Select a priority level for the selected cases:
          </p>
          <div className="grid grid-cols-2 gap-2">
            {(["critical", "high", "moderate", "low"] as CasePriority[]).map(
              (priority) => {
                const config = PRIORITY_CONFIG[priority];
                return (
                  <button
                    key={priority}
                    onClick={() => setSelectedPriority(priority)}
                    className={cn(
                      "flex items-center gap-2 p-3 rounded-lg border transition-colors",
                      selectedPriority === priority
                        ? "bg-primary/10 border-primary"
                        : "hover:bg-muted"
                    )}
                  >
                    <div
                      className={cn(
                        "h-3 w-3 rounded-full",
                        config.bgColor.replace("/10", "")
                      )}
                    />
                    <span className="font-medium">{config.label}</span>
                  </button>
                );
              }
            )}
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setActiveModal(null)}>
              Cancel
            </Button>
            <Button
              onClick={() =>
                handleAction("change_priority", { priority: selectedPriority })
              }
              disabled={isProcessing}
              isLoading={isProcessing}
            >
              Update Priority
            </Button>
          </div>
        </div>
      </Modal>

      {/* Change Status Modal */}
      <Modal
        isOpen={activeModal === "change_status"}
        onClose={() => setActiveModal(null)}
        title="Change Status"
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Select a status for the selected cases:
          </p>
          <div className="grid grid-cols-2 gap-2">
            {(
              ["pending", "in_progress", "review", "completed"] as CaseStatus[]
            ).map((status) => {
              const config = STATUS_CONFIG[status];
              return (
                <button
                  key={status}
                  onClick={() => setSelectedStatus(status)}
                  className={cn(
                    "flex items-center gap-2 p-3 rounded-lg border transition-colors",
                    selectedStatus === status
                      ? "bg-primary/10 border-primary"
                      : "hover:bg-muted"
                  )}
                >
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded text-xs",
                      config.bgColor,
                      config.color
                    )}
                  >
                    {config.label}
                  </span>
                </button>
              );
            })}
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setActiveModal(null)}>
              Cancel
            </Button>
            <Button
              onClick={() =>
                handleAction("change_status", { status: selectedStatus })
              }
              disabled={isProcessing}
              isLoading={isProcessing}
            >
              Update Status
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}

export default BulkActionsToolbar;
