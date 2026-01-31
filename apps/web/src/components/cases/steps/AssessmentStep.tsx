/**
 * NEURAXIS - Assessment Notes Step
 * Final clinical assessment with AI-powered differential diagnosis
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { useCaseForm } from "@/contexts/CaseFormContext";
import { cn } from "@/lib/utils";
import {
  assessmentNotesSchema,
  type AssessmentNotesInput,
} from "@/lib/validations/case";
import type { AISuggestion, UrgencyLevel } from "@/types/medical-case";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

const URGENCY_LEVELS: Array<{
  value: UrgencyLevel;
  label: string;
  color: string;
  description: string;
}> = [
  {
    value: "low",
    label: "Low",
    color: "bg-success",
    description: "Non-urgent, routine care",
  },
  {
    value: "moderate",
    label: "Moderate",
    color: "bg-warning",
    description: "Needs attention today",
  },
  {
    value: "high",
    label: "High",
    color: "bg-orange-500",
    description: "Requires immediate attention",
  },
  {
    value: "critical",
    label: "Critical",
    color: "bg-danger",
    description: "Life-threatening emergency",
  },
];

export function AssessmentStep() {
  const { state, setAssessment, canSubmit } = useCaseForm();
  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion | null>(null);
  const [isLoadingAI, setIsLoadingAI] = useState(false);
  const [newDiagnosis, setNewDiagnosis] = useState("");
  const [newTest, setNewTest] = useState("");

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<AssessmentNotesInput>({
    resolver: zodResolver(assessmentNotesSchema),
    defaultValues: state.assessment || {
      clinicalImpression: "",
      differentialDiagnosis: [],
      recommendedTests: [],
      treatmentPlan: "",
      followUpInstructions: "",
      urgencyLevel: "moderate",
    },
  });

  const differentialDiagnosis = watch("differentialDiagnosis");
  const recommendedTests = watch("recommendedTests");
  const urgencyLevel = watch("urgencyLevel");

  // Fetch AI suggestions
  useEffect(() => {
    const fetchAISuggestions = async () => {
      if (!state.chiefComplaint || state.symptoms.length === 0) return;

      setIsLoadingAI(true);
      try {
        const response = await fetch("/api/ai/analyze-case", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chiefComplaint: state.chiefComplaint,
            symptoms: state.symptoms,
            vitals: state.vitals,
            patientAge: state.patient?.age,
            patientGender: state.patient?.gender,
            medicalHistory: state.medicalHistory,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setAiSuggestions(data);

          // Auto-set urgency based on AI assessment
          if (data.urgencyAssessment?.level) {
            setValue("urgencyLevel", data.urgencyAssessment.level);
          }
        }
      } catch (error) {
        console.error("AI analysis error:", error);
      } finally {
        setIsLoadingAI(false);
      }
    };

    fetchAISuggestions();
  }, [
    state.chiefComplaint,
    state.symptoms,
    state.vitals,
    state.patient,
    state.medicalHistory,
    setValue,
  ]);

  const onSubmit = async (data: AssessmentNotesInput) => {
    setAssessment({
      ...data,
      aiSuggestions: aiSuggestions || undefined,
    });

    // Create the case
    try {
      const response = await fetch("/api/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient: state.patient,
          chiefComplaint: state.chiefComplaint,
          symptoms: state.symptoms,
          vitals: state.vitals,
          medicalHistory: state.medicalHistory,
          medications: state.medications,
          images: state.images,
          assessment: data,
        }),
      });

      if (!response.ok) throw new Error("Failed to create case");

      const result = await response.json();
      // Navigate to case view
      window.location.href = `/cases/${result.id}`;
    } catch (error) {
      console.error("Case creation error:", error);
    }
  };

  const addDiagnosis = () => {
    if (newDiagnosis.trim()) {
      setValue("differentialDiagnosis", [
        ...differentialDiagnosis,
        newDiagnosis.trim(),
      ]);
      setNewDiagnosis("");
    }
  };

  const removeDiagnosis = (index: number) => {
    setValue(
      "differentialDiagnosis",
      differentialDiagnosis.filter((_, i) => i !== index)
    );
  };

  const addTest = () => {
    if (newTest.trim()) {
      setValue("recommendedTests", [...recommendedTests, newTest.trim()]);
      setNewTest("");
    }
  };

  const removeTest = (index: number) => {
    setValue(
      "recommendedTests",
      recommendedTests.filter((_, i) => i !== index)
    );
  };

  const acceptAIDiagnosis = (diagnosis: string) => {
    if (!differentialDiagnosis.includes(diagnosis)) {
      setValue("differentialDiagnosis", [...differentialDiagnosis, diagnosis]);
    }
  };

  const acceptAITest = (test: string) => {
    if (!recommendedTests.includes(test)) {
      setValue("recommendedTests", [...recommendedTests, test]);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Clinical Assessment</h2>
        <p className="text-sm text-muted-foreground">
          Document your clinical findings and assessment
        </p>
      </div>

      {/* AI Analysis Panel */}
      {isLoadingAI ? (
        <div className="p-6 rounded-lg bg-primary/5 border border-primary/20 text-center">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-3" />
          <p className="font-medium">AI is analyzing the case...</p>
          <p className="text-sm text-muted-foreground">
            Generating differential diagnosis and urgency assessment
          </p>
        </div>
      ) : (
        aiSuggestions && (
          <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
            <div className="flex items-center gap-2 mb-4">
              <svg
                className="h-5 w-5 text-primary"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a2 2 0 0 1 0 4h-1v1a3 3 0 0 1-3 3h-8a3 3 0 0 1-3-3v-1H6a2 2 0 0 1 0-4h1V7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
              </svg>
              <h3 className="font-medium">AI Analysis</h3>
              <span className="text-xs text-muted-foreground">
                Confidence: {Math.round((aiSuggestions.confidence || 0) * 100)}%
              </span>
            </div>

            {/* Urgency Assessment */}
            {aiSuggestions.urgencyAssessment && (
              <div className="mb-4 p-3 rounded-lg bg-background border">
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded-full text-xs font-bold text-white",
                      URGENCY_LEVELS.find(
                        (u) => u.value === aiSuggestions.urgencyAssessment.level
                      )?.color
                    )}
                  >
                    {aiSuggestions.urgencyAssessment.level.toUpperCase()}{" "}
                    URGENCY
                  </span>
                </div>
                <p className="text-sm">
                  {aiSuggestions.urgencyAssessment.reasoning}
                </p>
                {aiSuggestions.urgencyAssessment.redFlags.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-danger mb-1">
                      Red Flags:
                    </p>
                    <ul className="text-xs text-danger list-disc list-inside">
                      {aiSuggestions.urgencyAssessment.redFlags.map(
                        (flag, i) => (
                          <li key={i}>{flag}</li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Suggested Diagnoses */}
            <div className="mb-4">
              <p className="text-xs font-medium mb-2">
                Suggested Differential Diagnoses:
              </p>
              <div className="flex flex-wrap gap-2">
                {aiSuggestions.differentialDiagnosis.map((dx, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => acceptAIDiagnosis(dx.diagnosis)}
                    disabled={differentialDiagnosis.includes(dx.diagnosis)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border transition-colors",
                      differentialDiagnosis.includes(dx.diagnosis)
                        ? "bg-success/10 border-success/30 text-success cursor-default"
                        : "hover:bg-primary/10 border-primary/30"
                    )}
                  >
                    <span>{dx.diagnosis}</span>
                    <span className="text-xs opacity-70">
                      {Math.round(dx.probability * 100)}%
                    </span>
                    {!differentialDiagnosis.includes(dx.diagnosis) && (
                      <svg
                        className="h-3 w-3"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Suggested Tests */}
            {aiSuggestions.differentialDiagnosis.some(
              (dx) => dx.suggestedTests.length > 0
            ) && (
              <div>
                <p className="text-xs font-medium mb-2">Suggested Tests:</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    ...new Set(
                      aiSuggestions.differentialDiagnosis.flatMap(
                        (dx) => dx.suggestedTests
                      )
                    ),
                  ].map((test, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => acceptAITest(test)}
                      disabled={recommendedTests.includes(test)}
                      className={cn(
                        "flex items-center gap-1 px-2 py-1 rounded text-xs border transition-colors",
                        recommendedTests.includes(test)
                          ? "bg-success/10 border-success/30 text-success"
                          : "hover:bg-muted border-input"
                      )}
                    >
                      {test}
                      {!recommendedTests.includes(test) && (
                        <svg
                          className="h-3 w-3"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <line x1="12" y1="5" x2="12" y2="19" />
                          <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      )}

      {/* Clinical Impression */}
      <div>
        <label className="text-sm font-medium mb-1.5 block">
          Clinical Impression *
        </label>
        <Textarea
          {...register("clinicalImpression")}
          placeholder="Document your clinical impression based on history, symptoms, and examination..."
          rows={4}
        />
        {errors.clinicalImpression && (
          <p className="text-xs text-danger mt-1">
            {errors.clinicalImpression.message}
          </p>
        )}
      </div>

      {/* Urgency Level */}
      <div>
        <label className="text-sm font-medium mb-3 block">
          Urgency Level *
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {URGENCY_LEVELS.map((level) => (
            <label
              key={level.value}
              className={cn(
                "p-3 rounded-lg border-2 cursor-pointer transition-all",
                urgencyLevel === level.value
                  ? `border-current ${level.color.replace("bg-", "text-")} ${level.color}/10`
                  : "border-muted hover:border-muted-foreground/50"
              )}
            >
              <input
                type="radio"
                value={level.value}
                {...register("urgencyLevel")}
                className="sr-only"
              />
              <div className="flex items-center gap-2 mb-1">
                <span className={cn("h-3 w-3 rounded-full", level.color)} />
                <span className="font-medium text-sm">{level.label}</span>
              </div>
              <p className="text-xs text-muted-foreground">
                {level.description}
              </p>
            </label>
          ))}
        </div>
      </div>

      {/* Differential Diagnosis */}
      <div>
        <label className="text-sm font-medium mb-1.5 block">
          Differential Diagnosis *
        </label>
        <div className="flex gap-2 mb-2">
          <Input
            placeholder="Add diagnosis..."
            value={newDiagnosis}
            onChange={(e) => setNewDiagnosis(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" && (e.preventDefault(), addDiagnosis())
            }
          />
          <Button type="button" variant="outline" onClick={addDiagnosis}>
            Add
          </Button>
        </div>
        {differentialDiagnosis.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {differentialDiagnosis.map((dx, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-sm bg-primary/10 text-primary"
              >
                {i + 1}. {dx}
                <button
                  type="button"
                  onClick={() => removeDiagnosis(i)}
                  className="p-0.5 rounded-full hover:bg-primary/20"
                >
                  <svg
                    className="h-3 w-3"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </span>
            ))}
          </div>
        )}
        {errors.differentialDiagnosis && (
          <p className="text-xs text-danger mt-1">
            {errors.differentialDiagnosis.message}
          </p>
        )}
      </div>

      {/* Recommended Tests */}
      <div>
        <label className="text-sm font-medium mb-1.5 block">
          Recommended Tests
        </label>
        <div className="flex gap-2 mb-2">
          <Input
            placeholder="Add test..."
            value={newTest}
            onChange={(e) => setNewTest(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" && (e.preventDefault(), addTest())
            }
          />
          <Button type="button" variant="outline" onClick={addTest}>
            Add
          </Button>
        </div>
        {recommendedTests.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {recommendedTests.map((test, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 px-2 py-1 rounded text-sm bg-muted"
              >
                {test}
                <button
                  type="button"
                  onClick={() => removeTest(i)}
                  className="p-0.5 rounded hover:bg-muted-foreground/20"
                >
                  <svg
                    className="h-3 w-3"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Treatment Plan & Follow-up */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium mb-1.5 block">
            Treatment Plan
          </label>
          <Textarea
            {...register("treatmentPlan")}
            placeholder="Outline the treatment plan..."
            rows={3}
          />
        </div>
        <div>
          <label className="text-sm font-medium mb-1.5 block">
            Follow-up Instructions
          </label>
          <Textarea
            {...register("followUpInstructions")}
            placeholder="Instructions for follow-up care..."
            rows={3}
          />
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={() => window.history.back()}
        >
          <svg
            className="h-4 w-4 mr-2"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back
        </Button>
        <Button
          type="submit"
          size="lg"
          disabled={!canSubmit()}
          isLoading={isSubmitting}
        >
          Create Case
          <svg
            className="h-4 w-4 ml-2"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </Button>
      </div>
    </form>
  );
}

export default AssessmentStep;
