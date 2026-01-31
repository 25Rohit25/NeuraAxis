/**
 * NEURAXIS - Bulk Actions Bar
 * Action bar for selected patients
 */

"use client";

import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/Modal";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface BulkActionsBarProps {
  selectedCount: number;
  onExport: () => void;
  onArchive: () => void;
  onActivate: () => void;
  onDelete: () => void;
  onClearSelection: () => void;
  isLoading?: boolean;
  className?: string;
}

export function BulkActionsBar({
  selectedCount,
  onExport,
  onArchive,
  onActivate,
  onDelete,
  onClearSelection,
  isLoading = false,
  className,
}: BulkActionsBarProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showArchiveConfirm, setShowArchiveConfirm] = useState(false);

  if (selectedCount === 0) return null;

  return (
    <>
      <div
        className={cn(
          "fixed bottom-4 left-1/2 -translate-x-1/2 z-40",
          "flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg",
          "bg-card border animate-slide-in-bottom",
          className
        )}
      >
        {/* Selection count */}
        <div className="flex items-center gap-2 pr-3 border-r">
          <span className="h-6 w-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center font-medium">
            {selectedCount}
          </span>
          <span className="text-sm font-medium">selected</span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            isLoading={isLoading}
            leftIcon={
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            }
          >
            Export
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onActivate}
            isLoading={isLoading}
            leftIcon={
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            }
          >
            Activate
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowArchiveConfirm(true)}
            isLoading={isLoading}
            leftIcon={
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
            }
          >
            Archive
          </Button>

          <Button
            variant="danger"
            size="sm"
            onClick={() => setShowDeleteConfirm(true)}
            isLoading={isLoading}
            leftIcon={
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            }
          >
            Delete
          </Button>
        </div>

        {/* Clear selection */}
        <button
          onClick={onClearSelection}
          className="p-1 rounded hover:bg-muted ml-1"
          aria-label="Clear selection"
        >
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Delete confirmation */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={() => {
          onDelete();
          setShowDeleteConfirm(false);
        }}
        title="Delete Patients"
        message={`Are you sure you want to delete ${selectedCount} patient${selectedCount > 1 ? "s" : ""}? This action cannot be undone.`}
        variant="danger"
        confirmText="Delete"
        isLoading={isLoading}
      />

      {/* Archive confirmation */}
      <ConfirmDialog
        isOpen={showArchiveConfirm}
        onClose={() => setShowArchiveConfirm(false)}
        onConfirm={() => {
          onArchive();
          setShowArchiveConfirm(false);
        }}
        title="Archive Patients"
        message={`Are you sure you want to archive ${selectedCount} patient${selectedCount > 1 ? "s" : ""}? They can be restored later.`}
        variant="warning"
        confirmText="Archive"
        isLoading={isLoading}
      />
    </>
  );
}

export default BulkActionsBar;
