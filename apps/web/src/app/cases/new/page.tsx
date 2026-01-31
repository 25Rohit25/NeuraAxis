/**
 * NEURAXIS - New Case Creation Page
 * Multi-step form for creating medical cases with AI assistance
 */

"use client";

import { ProgressIndicator } from "@/components/cases/ProgressIndicator";
import {
  AssessmentStep,
  ChiefComplaintStep,
  ImageUploadStep,
  MedicalHistoryStep,
  MedicationsStep,
  PatientSelectStep,
  SymptomCheckerStep,
  VitalSignsStep,
} from "@/components/cases/steps";
import { DashboardLayout } from "@/components/layout/Layout";
import { CaseFormProvider, useCaseForm } from "@/contexts/CaseFormContext";
import { formatRelativeTime } from "@/lib/utils";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

// Step components mapping
const STEP_COMPONENTS = [
  PatientSelectStep,
  ChiefComplaintStep,
  SymptomCheckerStep,
  VitalSignsStep,
  MedicalHistoryStep,
  MedicationsStep,
  ImageUploadStep,
  AssessmentStep,
];

function CaseCreationContent() {
  const { state, isSaving, saveError, saveDraft } = useCaseForm();
  const CurrentStepComponent = STEP_COMPONENTS[state.currentStep];

  return (
    <div className="min-h-screen pb-8">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b -mx-4 px-4 md:-mx-6 md:px-6 py-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
              <a href="/cases" className="hover:text-foreground">
                Cases
              </a>
              <span>/</span>
              <span>New Case</span>
            </div>
            <h1 className="text-2xl font-bold">Create Medical Case</h1>
          </div>

          {/* Auto-save status */}
          <div className="flex items-center gap-4">
            {state.isDirty && (
              <span className="text-sm text-warning flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-warning animate-pulse" />
                Unsaved changes
              </span>
            )}
            {isSaving && (
              <span className="text-sm text-muted-foreground flex items-center gap-2">
                <div className="h-3 w-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                Saving...
              </span>
            )}
            {state.lastSavedAt && !isSaving && !state.isDirty && (
              <span className="text-sm text-success flex items-center gap-1">
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                Saved {formatRelativeTime(state.lastSavedAt)}
              </span>
            )}
            {saveError && (
              <span className="text-sm text-danger">{saveError}</span>
            )}
            <button
              onClick={saveDraft}
              disabled={!state.isDirty || isSaving}
              className="text-sm px-3 py-1.5 rounded-lg border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save Draft
            </button>
          </div>
        </div>

        {/* Progress indicator */}
        <ProgressIndicator orientation="horizontal" />
      </div>

      {/* Main content */}
      <div className="max-w-3xl mx-auto">
        {/* Patient context bar */}
        {state.patient && (
          <div className="flex items-center gap-3 p-3 mb-6 rounded-lg bg-muted/50 border">
            <div className="h-10 w-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
              {state.patient.fullName
                .split(" ")
                .map((n) => n[0])
                .join("")
                .slice(0, 2)}
            </div>
            <div className="flex-1">
              <p className="font-medium">{state.patient.fullName}</p>
              <p className="text-sm text-muted-foreground">
                MRN: {state.patient.mrn} • {state.patient.age} yrs •{" "}
                {state.patient.gender}
              </p>
            </div>
            {state.chiefComplaint && (
              <div className="text-right">
                <p className="text-xs text-muted-foreground">Chief Complaint</p>
                <p className="text-sm font-medium truncate max-w-[200px]">
                  {state.chiefComplaint.complaint}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Current step */}
        <div className="bg-card rounded-xl border p-6 shadow-sm">
          <CurrentStepComponent />
        </div>

        {/* Keyboard shortcuts hint */}
        <div className="mt-4 text-center text-xs text-muted-foreground">
          Press{" "}
          <kbd className="px-1.5 py-0.5 rounded bg-muted border">Ctrl</kbd> +{" "}
          <kbd className="px-1.5 py-0.5 rounded bg-muted border">S</kbd> to save
          draft
        </div>
      </div>
    </div>
  );
}

function CaseCreationPageInner() {
  const searchParams = useSearchParams();
  const draftId = searchParams.get("draft");
  const patientId = searchParams.get("patient");

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        // Trigger save - will be handled by context
        document.querySelector<HTMLButtonElement>("[data-save-draft]")?.click();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <DashboardLayout>
      <CaseFormProvider
        initialDraftId={draftId || undefined}
        autoSaveIntervalMs={30000}
      >
        <CaseCreationContent />
      </CaseFormProvider>
    </DashboardLayout>
  );
}

export default function CaseCreationPage() {
  return (
    <Suspense fallback={<CaseCreationLoading />}>
      <CaseCreationPageInner />
    </Suspense>
  );
}

function CaseCreationLoading() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        {/* Header skeleton */}
        <div className="mb-6">
          <div className="h-4 w-24 bg-muted rounded mb-2" />
          <div className="h-8 w-48 bg-muted rounded" />
        </div>

        {/* Progress skeleton */}
        <div className="flex gap-4 mb-8">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-2">
              <div className="h-10 w-10 rounded-full bg-muted" />
              <div className="h-3 w-16 bg-muted rounded" />
            </div>
          ))}
        </div>

        {/* Content skeleton */}
        <div className="max-w-3xl mx-auto">
          <div className="h-96 rounded-xl bg-muted" />
        </div>
      </div>
    </DashboardLayout>
  );
}
