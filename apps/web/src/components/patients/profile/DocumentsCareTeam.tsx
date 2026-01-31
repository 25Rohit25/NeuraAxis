/**
 * NEURAXIS - Documents & Care Team Components
 * Document viewer and care team display
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { cn, formatDate, formatFileSize } from "@/lib/utils";
import type {
  CareTeamMember,
  CareTeamRole,
  DocumentCategory,
  PatientDocument,
} from "@/types/patient-profile";
import React, { useState } from "react";

// =============================================================================
// Document Viewer
// =============================================================================

interface DocumentViewerProps {
  documents: PatientDocument[];
  canUpload?: boolean;
  onUpload?: () => void;
  onDownload?: (document: PatientDocument) => void;
  isLoading?: boolean;
  className?: string;
}

const CATEGORY_LABELS: Record<DocumentCategory, string> = {
  insurance: "Insurance",
  consent: "Consent Forms",
  lab_report: "Lab Reports",
  imaging_report: "Imaging Reports",
  referral: "Referrals",
  discharge_summary: "Discharge",
  prescription: "Prescriptions",
  other: "Other",
};

const CATEGORY_ICONS: Record<DocumentCategory, React.ReactNode> = {
  insurance: (
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
  consent: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M9 15l2 2 4-4" />
    </svg>
  ),
  lab_report: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M14.5 2v6a2 2 0 0 0 2 2h6" />
      <path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6H6a2 2 0 0 0-2 2v5" />
    </svg>
  ),
  imaging_report: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  ),
  referral: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <polyline points="17 11 19 13 23 9" />
    </svg>
  ),
  discharge_summary: (
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
  ),
  prescription: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
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
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
};

const FILE_TYPE_ICONS: Record<string, React.ReactNode> = {
  pdf: <span className="text-danger font-bold text-xs">PDF</span>,
  jpg: <span className="text-blue-500 font-bold text-xs">JPG</span>,
  jpeg: <span className="text-blue-500 font-bold text-xs">JPG</span>,
  png: <span className="text-green-500 font-bold text-xs">PNG</span>,
  doc: <span className="text-blue-600 font-bold text-xs">DOC</span>,
  docx: <span className="text-blue-600 font-bold text-xs">DOC</span>,
};

export function DocumentViewer({
  documents,
  canUpload = false,
  onUpload,
  onDownload,
  isLoading = false,
  className,
}: DocumentViewerProps) {
  const [selectedCategory, setSelectedCategory] = useState<
    DocumentCategory | "all"
  >("all");
  const [selectedDocument, setSelectedDocument] =
    useState<PatientDocument | null>(null);

  const filteredDocuments =
    selectedCategory === "all"
      ? documents
      : documents.filter((doc) => doc.category === selectedCategory);

  const categoryCounts = documents.reduce(
    (acc, doc) => {
      acc[doc.category] = (acc[doc.category] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  if (isLoading) {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-3 rounded-lg border animate-pulse">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded bg-muted" />
              <div className="flex-1">
                <div className="h-4 w-1/2 bg-muted rounded mb-1" />
                <div className="h-3 w-1/3 bg-muted rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Documents ({documents.length})
        </h3>
        {canUpload && onUpload && (
          <Button size="xs" onClick={onUpload}>
            Upload
          </Button>
        )}
      </div>

      {/* Category filter */}
      <div className="flex gap-1 mb-4 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedCategory("all")}
          className={cn(
            "px-2 py-1 text-xs rounded whitespace-nowrap transition-colors",
            selectedCategory === "all"
              ? "bg-primary text-primary-foreground"
              : "hover:bg-muted"
          )}
        >
          All
        </button>
        {(Object.keys(CATEGORY_LABELS) as DocumentCategory[]).map((cat) => {
          const count = categoryCounts[cat] || 0;
          if (count === 0) return null;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                "flex items-center gap-1 px-2 py-1 text-xs rounded whitespace-nowrap transition-colors",
                selectedCategory === cat
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              )}
            >
              {CATEGORY_LABELS[cat]} ({count})
            </button>
          );
        })}
      </div>

      {/* Documents list */}
      {filteredDocuments.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground bg-muted/30 rounded-lg">
          <svg
            className="h-10 w-10 mx-auto mb-2 opacity-50"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <p>No documents found</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              onClick={() => setSelectedDocument(doc)}
              className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-muted/30 cursor-pointer transition-colors"
            >
              {/* Icon */}
              <div className="h-10 w-10 rounded bg-muted flex items-center justify-center shrink-0">
                {FILE_TYPE_ICONS[doc.fileType.toLowerCase()] ||
                  CATEGORY_ICONS[doc.category]}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{doc.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatDate(doc.uploadDate)} • {formatFileSize(doc.fileSize)}
                </p>
              </div>

              {/* Confidential badge */}
              {doc.isConfidential && (
                <span className="px-1.5 py-0.5 rounded text-xs bg-danger/10 text-danger">
                  Confidential
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Document preview modal */}
      <Modal
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        title={selectedDocument?.name || ""}
        size="lg"
      >
        {selectedDocument && (
          <div className="space-y-4">
            {/* Preview area */}
            <div className="aspect-[4/3] rounded-lg bg-muted flex items-center justify-center overflow-hidden">
              {selectedDocument.thumbnailUrl ? (
                <img
                  src={selectedDocument.thumbnailUrl}
                  alt={selectedDocument.name}
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-center">
                  <div className="h-16 w-16 mx-auto mb-2 rounded bg-muted-foreground/10 flex items-center justify-center">
                    {CATEGORY_ICONS[selectedDocument.category]}
                  </div>
                  <p className="text-muted-foreground text-sm">
                    Preview not available
                  </p>
                </div>
              )}
            </div>

            {/* Details */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Category</p>
                <p>{CATEGORY_LABELS[selectedDocument.category]}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">File Type</p>
                <p>{selectedDocument.fileType.toUpperCase()}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Size</p>
                <p>{formatFileSize(selectedDocument.fileSize)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Uploaded</p>
                <p>{formatDate(selectedDocument.uploadDate)}</p>
              </div>
            </div>

            {selectedDocument.description && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">
                  Description
                </p>
                <p className="text-sm">{selectedDocument.description}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-2 border-t">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => window.open(selectedDocument.url, "_blank")}
              >
                Open
              </Button>
              <Button
                className="flex-1"
                onClick={() => {
                  onDownload?.(selectedDocument);
                  setSelectedDocument(null);
                }}
              >
                Download
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

// =============================================================================
// Care Team
// =============================================================================

interface CareTeamProps {
  members: CareTeamMember[];
  canEdit?: boolean;
  onAddMember?: () => void;
  onContactMember?: (member: CareTeamMember) => void;
  isLoading?: boolean;
  className?: string;
}

const ROLE_LABELS: Record<CareTeamRole, string> = {
  primary_care: "Primary Care",
  specialist: "Specialist",
  surgeon: "Surgeon",
  nurse: "Nurse",
  pharmacist: "Pharmacist",
  therapist: "Therapist",
  dietitian: "Dietitian",
  case_manager: "Case Manager",
  other: "Other",
};

export function CareTeam({
  members,
  canEdit = false,
  onAddMember,
  onContactMember,
  isLoading = false,
  className,
}: CareTeamProps) {
  // Sort to show primary first
  const sortedMembers = [...members].sort((a, b) => {
    if (a.isPrimary && !b.isPrimary) return -1;
    if (!a.isPrimary && b.isPrimary) return 1;
    return 0;
  });

  if (isLoading) {
    return (
      <div className={cn("space-y-3", className)}>
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="flex items-center gap-3 p-3 rounded-lg border animate-pulse"
          >
            <div className="h-10 w-10 rounded-full bg-muted" />
            <div className="flex-1">
              <div className="h-4 w-1/3 bg-muted rounded mb-1" />
              <div className="h-3 w-1/2 bg-muted rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          Care Team ({members.length})
        </h3>
        {canEdit && onAddMember && (
          <Button size="xs" variant="outline" onClick={onAddMember}>
            Add
          </Button>
        )}
      </div>

      {/* Team members */}
      {sortedMembers.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground bg-muted/30 rounded-lg">
          <p>No care team assigned</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sortedMembers.map((member) => (
            <div
              key={member.id}
              className="flex items-center gap-3 p-3 rounded-lg border bg-card"
            >
              {/* Avatar */}
              <div
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center text-sm font-medium shrink-0",
                  member.isPrimary
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                )}
              >
                {member.photoUrl ? (
                  <img
                    src={member.photoUrl}
                    alt={member.name}
                    className="h-full w-full rounded-full object-cover"
                  />
                ) : (
                  member.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                )}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium truncate">{member.name}</p>
                  {member.isPrimary && (
                    <span className="px-1.5 py-0.5 rounded text-xs bg-primary/10 text-primary">
                      Primary
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  {ROLE_LABELS[member.role]}
                  {member.specialty && ` • ${member.specialty}`}
                </p>
              </div>

              {/* Contact button */}
              {(member.phone || member.email) && onContactMember && (
                <button
                  onClick={() => onContactMember(member)}
                  className="p-2 rounded hover:bg-muted"
                  aria-label={`Contact ${member.name}`}
                >
                  <svg
                    className="h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                  </svg>
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export { CareTeam, DocumentViewer };
