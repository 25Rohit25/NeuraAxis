/**
 * NEURAXIS - Case Detail Page
 * Comprehensive case view with collaboration features
 */

"use client";

import {
  AIAnalysisPanel,
  CaseTimeline,
  ClinicalNotesEditor,
  CommentSection,
  ImageGallery,
  LabResultsTable,
  PresenceIndicators,
  TreatmentPlanEditor,
  VersionHistoryPanel,
} from "@/components/cases/detail";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import { useCaseDetail, usePresence } from "@/hooks/useCaseDetail";
import { cn, formatRelativeTime, getInitials } from "@/lib/utils";
import type { ExportOptions } from "@/types/case-detail";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

// =============================================================================
// Section Navigation
// =============================================================================

const SECTIONS = [
  { id: "overview", label: "Overview", icon: "home" },
  { id: "timeline", label: "Timeline", icon: "clock" },
  { id: "notes", label: "Clinical Notes", icon: "file-text" },
  { id: "ai", label: "AI Analysis", icon: "cpu" },
  { id: "treatment", label: "Treatment Plan", icon: "activity" },
  { id: "images", label: "Medical Images", icon: "image" },
  { id: "labs", label: "Lab Results", icon: "flask" },
  { id: "documents", label: "Documents", icon: "folder" },
];

// =============================================================================
// Main Page Component
// =============================================================================

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  // State
  const [activeSection, setActiveSection] = useState("overview");
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isPrintMode, setIsPrintMode] = useState(false);

  // Hooks
  const caseDetail = useCaseDetail({ caseId, enableRealtime: true });
  const presence = usePresence({
    caseId,
    userId: "current-user-id", // Would come from auth
    userName: "Dr. Current User",
  });

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case "s":
            e.preventDefault();
            // Save is automatic
            break;
          case "p":
            e.preventDefault();
            handlePrint();
            break;
          case "e":
            e.preventDefault();
            setIsExportModalOpen(true);
            break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Handlers
  const handleExport = async (options: ExportOptions) => {
    try {
      await caseDetail.exportCase(options);
      setIsExportModalOpen(false);
    } catch (err) {
      console.error("Export failed:", err);
    }
  };

  const handlePrint = () => {
    setIsPrintMode(true);
    setTimeout(() => {
      window.print();
      setIsPrintMode(false);
    }, 100);
  };

  // Loading state
  if (caseDetail.isLoading) {
    return <CaseDetailSkeleton />;
  }

  // Error state
  if (caseDetail.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-bold text-danger mb-2">
            Error Loading Case
          </h2>
          <p className="text-muted-foreground mb-4">{caseDetail.error}</p>
          <Button onClick={caseDetail.refreshCase}>Retry</Button>
        </div>
      </div>
    );
  }

  if (!caseDetail.caseData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Case not found</p>
      </div>
    );
  }

  const { caseData } = caseDetail;

  return (
    <div
      className={cn("min-h-screen bg-background", isPrintMode && "print-mode")}
    >
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur">
        <div className="px-6 py-4">
          {/* Top bar */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/cases")}
              >
                <svg
                  className="h-4 w-4 mr-1"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <polyline points="15 18 9 12 15 6" />
                </svg>
                Back
              </Button>

              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold">{caseData.caseNumber}</h1>
                  <StatusBadge status={caseData.status} />
                  <PriorityBadge priority={caseData.priority} />
                </div>
                <p className="text-sm text-muted-foreground">
                  Created {formatRelativeTime(caseData.createdAt)} • Last
                  updated {formatRelativeTime(caseData.updatedAt)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Presence indicators */}
              <PresenceIndicators
                users={presence.activeUsers}
                isConnected={presence.isConnected}
              />

              {/* Save status */}
              {caseDetail.isSaving && (
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <svg
                    className="h-4 w-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M21 12a9 9 0 11-6.219-8.56" />
                  </svg>
                  Saving...
                </span>
              )}

              {/* Lock indicator */}
              {caseDetail.isLocked && caseDetail.lockedBy && (
                <span className="px-3 py-1 rounded-full bg-warning/10 text-warning text-sm flex items-center gap-1">
                  <svg
                    className="h-4 w-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                  Locked by {caseDetail.lockedBy}
                </span>
              )}

              {/* Actions */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsHistoryOpen(true)}
              >
                <svg
                  className="h-4 w-4 mr-1"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                History
              </Button>

              <Button variant="outline" size="sm" onClick={handlePrint}>
                <svg
                  className="h-4 w-4 mr-1"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <polyline points="6 9 6 2 18 2 18 9" />
                  <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                  <rect x="6" y="14" width="12" height="8" />
                </svg>
                Print
              </Button>

              <Button size="sm" onClick={() => setIsExportModalOpen(true)}>
                <svg
                  className="h-4 w-4 mr-1"
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
            </div>
          </div>

          {/* Patient info bar */}
          <div className="flex items-center gap-6 p-4 rounded-lg bg-muted/50">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-lg font-bold text-primary">
                {getInitials(caseData.patient.fullName)}
              </span>
            </div>
            <div>
              <h2 className="font-semibold">{caseData.patient.fullName}</h2>
              <p className="text-sm text-muted-foreground">
                {caseData.patient.age}y {caseData.patient.gender} • MRN:{" "}
                {caseData.patient.mrn} •
                {caseData.patient.bloodType &&
                  ` Blood: ${caseData.patient.bloodType}`}
              </p>
            </div>
            <div className="ml-auto flex items-center gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Assigned: </span>
                <span className="font-medium">
                  Dr. {caseData.assignedTo.lastName}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Created by: </span>
                <span className="font-medium">
                  Dr. {caseData.createdBy.lastName}
                </span>
              </div>
            </div>
          </div>

          {/* Section tabs */}
          <div className="flex items-center gap-1 mt-4 overflow-x-auto pb-2">
            {SECTIONS.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap",
                  activeSection === section.id
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                {section.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="p-6">
        {activeSection === "overview" && (
          <CaseOverview caseData={caseData} onSectionClick={setActiveSection} />
        )}

        {activeSection === "timeline" && (
          <CaseTimeline caseId={caseId} initialEvents={caseDetail.timeline} />
        )}

        {activeSection === "notes" && (
          <ClinicalNotesEditor
            caseId={caseId}
            notes={caseData.clinicalNotes}
            onUpdate={(data) => caseDetail.updateSection("clinicalNotes", data)}
            presence={presence}
          />
        )}

        {activeSection === "ai" && (
          <AIAnalysisPanel
            analysis={caseData.aiAnalysis}
            onRerun={() =>
              caseDetail.updateSection("aiAnalysis", { rerun: true })
            }
          />
        )}

        {activeSection === "treatment" && (
          <TreatmentPlanEditor
            plan={caseData.treatmentPlan}
            onUpdate={(data) => caseDetail.updateSection("treatmentPlan", data)}
          />
        )}

        {activeSection === "images" && (
          <ImageGallery
            images={caseData.images}
            caseId={caseId}
            onUpdate={(data) => caseDetail.updateSection("images", data)}
          />
        )}

        {activeSection === "labs" && (
          <LabResultsTable
            results={caseData.labResults}
            onAddResult={() => {}}
          />
        )}

        {activeSection === "documents" && (
          <DocumentsSection documents={caseData.documents} caseId={caseId} />
        )}
      </main>

      {/* Comments sidebar */}
      <CommentSection
        caseId={caseId}
        threads={caseDetail.comments}
        onAddComment={caseDetail.addComment}
        onResolveThread={caseDetail.resolveThread}
      />

      {/* Export modal */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        onExport={handleExport}
        caseNumber={caseData.caseNumber}
      />

      {/* Version history */}
      <VersionHistoryPanel
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        versions={caseDetail.versionHistory}
        onRevert={caseDetail.revertToVersion}
        onCompare={caseDetail.compareVersions}
      />
    </div>
  );
}

// =============================================================================
// Case Overview Section
// =============================================================================

interface CaseOverviewProps {
  caseData: any;
  onSectionClick: (section: string) => void;
}

function CaseOverview({ caseData, onSectionClick }: CaseOverviewProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left column - Clinical info */}
      <div className="lg:col-span-2 space-y-6">
        {/* Chief complaint */}
        <div className="bg-card rounded-xl border p-6">
          <h3 className="font-semibold mb-4">Chief Complaint</h3>
          <p className="text-lg">{caseData.chiefComplaint?.complaint}</p>
          <div className="flex flex-wrap gap-4 mt-4 text-sm text-muted-foreground">
            {caseData.chiefComplaint?.duration && (
              <span>
                Duration: {caseData.chiefComplaint.duration}{" "}
                {caseData.chiefComplaint.durationUnit}
              </span>
            )}
            {caseData.chiefComplaint?.onset && (
              <span>Onset: {caseData.chiefComplaint.onset}</span>
            )}
            {caseData.chiefComplaint?.severity && (
              <span>Severity: {caseData.chiefComplaint.severity}/10</span>
            )}
          </div>
        </div>

        {/* Vitals */}
        {caseData.vitals && (
          <div className="bg-card rounded-xl border p-6">
            <h3 className="font-semibold mb-4">Vital Signs</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <VitalCard
                label="Blood Pressure"
                value={`${caseData.vitals.bloodPressureSystolic}/${caseData.vitals.bloodPressureDiastolic}`}
                unit="mmHg"
              />
              <VitalCard
                label="Heart Rate"
                value={caseData.vitals.heartRate}
                unit="bpm"
              />
              <VitalCard
                label="Temperature"
                value={caseData.vitals.temperature}
                unit={`°${caseData.vitals.temperatureUnit}`}
              />
              <VitalCard
                label="SpO2"
                value={caseData.vitals.oxygenSaturation}
                unit="%"
              />
            </div>
          </div>
        )}

        {/* Symptoms */}
        {caseData.symptoms?.length > 0 && (
          <div className="bg-card rounded-xl border p-6">
            <h3 className="font-semibold mb-4">
              Symptoms ({caseData.symptoms.length})
            </h3>
            <div className="flex flex-wrap gap-2">
              {caseData.symptoms.map((symptom: any) => (
                <span
                  key={symptom.id}
                  className={cn(
                    "px-3 py-1 rounded-full text-sm",
                    symptom.severity >= 8
                      ? "bg-danger/10 text-danger"
                      : symptom.severity >= 5
                        ? "bg-warning/10 text-warning"
                        : "bg-muted text-muted-foreground"
                  )}
                >
                  {symptom.name}
                  {symptom.isAISuggested && (
                    <svg
                      className="inline h-3 w-3 ml-1 text-primary"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                    >
                      <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a2 2 0 0 1 0 4h-1v1a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-1H6a2 2 0 0 1 0-4h1V7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
                    </svg>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* AI Analysis preview */}
        {caseData.aiAnalysis && (
          <div
            className="bg-gradient-to-br from-primary/5 to-primary/10 rounded-xl border border-primary/20 p-6 cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => onSectionClick("ai")}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold flex items-center gap-2">
                <svg
                  className="h-5 w-5 text-primary"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a2 2 0 0 1 0 4h-1v1a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-1H6a2 2 0 0 1 0-4h1V7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
                </svg>
                AI Analysis
              </h3>
              <span className="text-xs text-muted-foreground">
                Confidence: {(caseData.aiAnalysis.confidence * 100).toFixed(0)}%
              </span>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium">Top Differential Diagnosis:</p>
              {caseData.aiAnalysis.differentialDiagnosis
                ?.slice(0, 3)
                .map((dx: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center justify-between text-sm"
                  >
                    <span>{dx.diagnosis}</span>
                    <span className="text-muted-foreground">
                      {(dx.probability * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
            </div>

            <p className="text-sm text-primary mt-4 flex items-center">
              View full analysis
              <svg
                className="h-4 w-4 ml-1"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </p>
          </div>
        )}
      </div>

      {/* Right column - Sidebar info */}
      <div className="space-y-6">
        {/* Treatment plan preview */}
        {caseData.treatmentPlan && (
          <div
            className="bg-card rounded-xl border p-6 cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => onSectionClick("treatment")}
          >
            <h3 className="font-semibold mb-4">Treatment Plan</h3>

            {caseData.treatmentPlan.diagnosis?.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-muted-foreground uppercase mb-2">
                  Diagnosis
                </p>
                {caseData.treatmentPlan.diagnosis.slice(0, 2).map((dx: any) => (
                  <p key={dx.id} className="text-sm">
                    {dx.description}
                  </p>
                ))}
              </div>
            )}

            {caseData.treatmentPlan.medications?.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-muted-foreground uppercase mb-2">
                  Medications
                </p>
                <p className="text-sm">
                  {caseData.treatmentPlan.medications.length} prescribed
                </p>
              </div>
            )}

            {caseData.treatmentPlan.followUp && (
              <div>
                <p className="text-xs text-muted-foreground uppercase mb-2">
                  Follow-up
                </p>
                <p className="text-sm">
                  {caseData.treatmentPlan.followUp.reason}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Medical images preview */}
        {caseData.images?.length > 0 && (
          <div
            className="bg-card rounded-xl border p-6 cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => onSectionClick("images")}
          >
            <h3 className="font-semibold mb-4">
              Medical Images ({caseData.images.length})
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {caseData.images.slice(0, 6).map((img: any) => (
                <div
                  key={img.id}
                  className="aspect-square rounded-lg bg-muted overflow-hidden"
                >
                  <img
                    src={img.thumbnailUrl || img.url}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Lab results preview */}
        {caseData.labResults?.length > 0 && (
          <div
            className="bg-card rounded-xl border p-6 cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => onSectionClick("labs")}
          >
            <h3 className="font-semibold mb-4">
              Lab Results ({caseData.labResults.length})
            </h3>
            <div className="space-y-2">
              {caseData.labResults.slice(0, 4).map((lab: any) => (
                <div
                  key={lab.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="truncate">{lab.testName}</span>
                  <span
                    className={cn(
                      "font-medium",
                      lab.status === "normal" && "text-success",
                      lab.status === "high" && "text-danger",
                      lab.status === "low" && "text-warning",
                      lab.status === "critical" && "text-danger animate-pulse"
                    )}
                  >
                    {lab.value} {lab.unit}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Care team */}
        {caseData.careTeam?.length > 0 && (
          <div className="bg-card rounded-xl border p-6">
            <h3 className="font-semibold mb-4">Care Team</h3>
            <div className="space-y-3">
              {caseData.careTeam.map((member: any) => (
                <div key={member.id} className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-xs font-bold text-primary">
                      {getInitials(member.fullName)}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Dr. {member.lastName}</p>
                    <p className="text-xs text-muted-foreground">
                      {member.specialty}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function VitalCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: any;
  unit: string;
}) {
  return (
    <div className="p-3 rounded-lg bg-muted/50">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-bold">
        {value}{" "}
        <span className="text-sm font-normal text-muted-foreground">
          {unit}
        </span>
      </p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; text: string; label: string }> = {
    draft: { bg: "bg-muted", text: "text-muted-foreground", label: "Draft" },
    pending: { bg: "bg-warning/10", text: "text-warning", label: "Pending" },
    in_progress: { bg: "bg-info/10", text: "text-info", label: "In Progress" },
    review: {
      bg: "bg-purple-500/10",
      text: "text-purple-500",
      label: "Review",
    },
    completed: {
      bg: "bg-success/10",
      text: "text-success",
      label: "Completed",
    },
    archived: {
      bg: "bg-muted",
      text: "text-muted-foreground",
      label: "Archived",
    },
  };
  const c = config[status] || config.pending;
  return (
    <span
      className={cn(
        "px-2 py-0.5 rounded-full text-xs font-medium",
        c.bg,
        c.text
      )}
    >
      {c.label}
    </span>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const config: Record<string, { bg: string; text: string; label: string }> = {
    low: { bg: "bg-success/10", text: "text-success", label: "Low" },
    moderate: { bg: "bg-warning/10", text: "text-warning", label: "Moderate" },
    high: { bg: "bg-orange-500/10", text: "text-orange-500", label: "High" },
    critical: { bg: "bg-danger/10", text: "text-danger", label: "Critical" },
  };
  const c = config[priority] || config.moderate;
  return (
    <span
      className={cn(
        "px-2 py-0.5 rounded-full text-xs font-medium",
        c.bg,
        c.text
      )}
    >
      {c.label}
    </span>
  );
}

function DocumentsSection({
  documents,
  caseId,
}: {
  documents: any[];
  caseId: string;
}) {
  return (
    <div className="bg-card rounded-xl border p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Documents</h3>
        <Button size="sm">
          <svg
            className="h-4 w-4 mr-2"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Generate Report
        </Button>
      </div>

      {documents?.length > 0 ? (
        <div className="space-y-3">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <svg
                    className="h-5 w-5 text-primary"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium">{doc.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {doc.type} • {formatRelativeTime(doc.generatedAt)}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm">
                Download
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-muted-foreground">
          No documents generated yet
        </div>
      )}
    </div>
  );
}

// Export modal
interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (options: ExportOptions) => void;
  caseNumber: string;
}

function ExportModal({
  isOpen,
  onClose,
  onExport,
  caseNumber,
}: ExportModalProps) {
  const [options, setOptions] = useState<ExportOptions>({
    format: "pdf",
    sections: ["all"],
    includeImages: true,
    includeAIAnalysis: true,
    includeComments: false,
    isPrintOptimized: false,
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Export ${caseNumber}`}>
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">Format</label>
          <div className="flex gap-2 mt-2">
            {(["pdf", "docx", "html"] as const).map((format) => (
              <button
                key={format}
                onClick={() => setOptions((o) => ({ ...o, format }))}
                className={cn(
                  "px-4 py-2 rounded-lg border text-sm font-medium transition-colors",
                  options.format === format
                    ? "bg-primary text-primary-foreground border-primary"
                    : "hover:bg-muted"
                )}
              >
                {format.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={options.includeImages}
              onChange={(e) =>
                setOptions((o) => ({ ...o, includeImages: e.target.checked }))
              }
            />
            <span className="text-sm">Include medical images</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={options.includeAIAnalysis}
              onChange={(e) =>
                setOptions((o) => ({
                  ...o,
                  includeAIAnalysis: e.target.checked,
                }))
              }
            />
            <span className="text-sm">Include AI analysis</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={options.includeComments}
              onChange={(e) =>
                setOptions((o) => ({ ...o, includeComments: e.target.checked }))
              }
            />
            <span className="text-sm">Include comments</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={options.isPrintOptimized}
              onChange={(e) =>
                setOptions((o) => ({
                  ...o,
                  isPrintOptimized: e.target.checked,
                }))
              }
            />
            <span className="text-sm">Print-optimized layout</span>
          </label>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => onExport(options)}>Export</Button>
        </div>
      </div>
    </Modal>
  );
}

// Loading skeleton
function CaseDetailSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card p-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Skeleton className="h-20 mt-4" />
        <div className="flex gap-2 mt-4">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-24" />
          ))}
        </div>
      </header>
      <main className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-48" />
            <Skeleton className="h-32" />
            <Skeleton className="h-64" />
          </div>
          <div className="space-y-6">
            <Skeleton className="h-48" />
            <Skeleton className="h-48" />
          </div>
        </div>
      </main>
    </div>
  );
}
