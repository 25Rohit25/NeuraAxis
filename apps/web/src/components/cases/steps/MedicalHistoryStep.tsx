/**
 * NEURAXIS - Medical History Step
 * Review and edit patient medical history
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCaseForm } from "@/contexts/CaseFormContext";
import { cn } from "@/lib/utils";
import type { MedicalHistory, MedicalHistoryItem } from "@/types/medical-case";
import { useEffect, useState } from "react";

export function MedicalHistoryStep() {
  const { state, setMedicalHistory, nextStep, prevStep } = useCaseForm();
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState<MedicalHistory>(
    state.medicalHistory || {
      conditions: [],
      allergies: [],
      surgeries: [],
      familyHistory: [],
    }
  );

  // Fetch from patient record
  useEffect(() => {
    const fetchPatientHistory = async () => {
      if (!state.patient?.patientId) return;

      setIsLoading(true);
      try {
        const response = await fetch(
          `/api/patients/${state.patient.patientId}/history`
        );
        if (response.ok) {
          const data = await response.json();
          setHistory({
            conditions: (data.conditions || []).map((c: any) => ({
              ...c,
              isFromPatientRecord: true,
            })),
            allergies: (data.allergies || []).map((a: any) => ({
              ...a,
              isFromPatientRecord: true,
            })),
            surgeries: (data.surgeries || []).map((s: any) => ({
              ...s,
              isFromPatientRecord: true,
            })),
            familyHistory: (data.familyHistory || []).map((f: any) => ({
              ...f,
              isFromPatientRecord: true,
            })),
          });
        }
      } catch (error) {
        console.error("Failed to fetch patient history:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (!state.medicalHistory) {
      fetchPatientHistory();
    }
  }, [state.patient, state.medicalHistory]);

  // Add new condition
  const addCondition = () => {
    const newCondition: MedicalHistoryItem = {
      id: `cond-${Date.now()}`,
      condition: "",
      status: "active",
      isFromPatientRecord: false,
    };
    setHistory((prev) => ({
      ...prev,
      conditions: [...prev.conditions, newCondition],
    }));
  };

  const updateCondition = (id: string, field: string, value: any) => {
    setHistory((prev) => ({
      ...prev,
      conditions: prev.conditions.map((c) =>
        c.id === id ? { ...c, [field]: value } : c
      ),
    }));
  };

  const removeCondition = (id: string) => {
    setHistory((prev) => ({
      ...prev,
      conditions: prev.conditions.filter((c) => c.id !== id),
    }));
  };

  // Add new allergy
  const addAllergy = () => {
    const newAllergy = {
      id: `allergy-${Date.now()}`,
      allergen: "",
      severity: "moderate",
      reaction: "",
      isFromPatientRecord: false,
    };
    setHistory((prev) => ({
      ...prev,
      allergies: [...prev.allergies, newAllergy],
    }));
  };

  const updateAllergy = (id: string, field: string, value: any) => {
    setHistory((prev) => ({
      ...prev,
      allergies: prev.allergies.map((a) =>
        a.id === id ? { ...a, [field]: value } : a
      ),
    }));
  };

  const removeAllergy = (id: string) => {
    setHistory((prev) => ({
      ...prev,
      allergies: prev.allergies.filter((a) => a.id !== id),
    }));
  };

  // Add new surgery
  const addSurgery = () => {
    const newSurgery = {
      id: `surg-${Date.now()}`,
      procedure: "",
      date: "",
      notes: "",
      isFromPatientRecord: false,
    };
    setHistory((prev) => ({
      ...prev,
      surgeries: [...prev.surgeries, newSurgery],
    }));
  };

  const updateSurgery = (id: string, field: string, value: any) => {
    setHistory((prev) => ({
      ...prev,
      surgeries: prev.surgeries.map((s) =>
        s.id === id ? { ...s, [field]: value } : s
      ),
    }));
  };

  const removeSurgery = (id: string) => {
    setHistory((prev) => ({
      ...prev,
      surgeries: prev.surgeries.filter((s) => s.id !== id),
    }));
  };

  const handleContinue = () => {
    setMedicalHistory(history);
    nextStep();
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold mb-1">Medical History</h2>
          <p className="text-sm text-muted-foreground">
            Loading patient records...
          </p>
        </div>
        <div className="flex justify-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Medical History</h2>
        <p className="text-sm text-muted-foreground">
          Review and update patient's medical history
        </p>
      </div>

      {/* Conditions */}
      <div className="p-4 rounded-lg border bg-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Medical Conditions</h3>
          <Button size="sm" variant="outline" onClick={addCondition}>
            + Add
          </Button>
        </div>

        {history.conditions.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No conditions documented
          </p>
        ) : (
          <div className="space-y-3">
            {history.conditions.map((condition) => (
              <div
                key={condition.id}
                className={cn(
                  "p-3 rounded-lg border flex items-start gap-3",
                  condition.isFromPatientRecord && "bg-muted/30"
                )}
              >
                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input
                    placeholder="Condition name"
                    value={condition.condition}
                    onChange={(e) =>
                      updateCondition(condition.id, "condition", e.target.value)
                    }
                  />
                  <select
                    value={condition.status}
                    onChange={(e) =>
                      updateCondition(condition.id, "status", e.target.value)
                    }
                    className="h-10 px-3 rounded-md border bg-background"
                  >
                    <option value="active">Active</option>
                    <option value="chronic">Chronic</option>
                    <option value="resolved">Resolved</option>
                  </select>
                  <Input
                    type="date"
                    placeholder="Diagnosis date"
                    value={condition.diagnosisDate || ""}
                    onChange={(e) =>
                      updateCondition(
                        condition.id,
                        "diagnosisDate",
                        e.target.value
                      )
                    }
                  />
                </div>
                {condition.isFromPatientRecord && (
                  <span className="text-xs text-muted-foreground shrink-0">
                    From record
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => removeCondition(condition.id)}
                  className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-danger shrink-0"
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
            ))}
          </div>
        )}
      </div>

      {/* Allergies */}
      <div className="p-4 rounded-lg border bg-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium flex items-center gap-2">
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
            Allergies
          </h3>
          <Button size="sm" variant="outline" onClick={addAllergy}>
            + Add
          </Button>
        </div>

        {history.allergies.length === 0 ? (
          <div className="py-4 text-center">
            <p className="text-sm text-success">No Known Allergies (NKA)</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.allergies.map((allergy) => (
              <div
                key={allergy.id}
                className={cn(
                  "p-3 rounded-lg border flex items-start gap-3",
                  allergy.isFromPatientRecord && "bg-danger/5 border-danger/20"
                )}
              >
                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input
                    placeholder="Allergen"
                    value={allergy.allergen}
                    onChange={(e) =>
                      updateAllergy(allergy.id, "allergen", e.target.value)
                    }
                  />
                  <select
                    value={allergy.severity}
                    onChange={(e) =>
                      updateAllergy(allergy.id, "severity", e.target.value)
                    }
                    className="h-10 px-3 rounded-md border bg-background"
                  >
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                    <option value="life_threatening">Life-threatening</option>
                  </select>
                  <Input
                    placeholder="Reaction"
                    value={allergy.reaction}
                    onChange={(e) =>
                      updateAllergy(allergy.id, "reaction", e.target.value)
                    }
                  />
                </div>
                {allergy.isFromPatientRecord && (
                  <span className="text-xs text-danger shrink-0">
                    From record
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => removeAllergy(allergy.id)}
                  className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-danger shrink-0"
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
            ))}
          </div>
        )}
      </div>

      {/* Surgical History */}
      <div className="p-4 rounded-lg border bg-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Surgical History</h3>
          <Button size="sm" variant="outline" onClick={addSurgery}>
            + Add
          </Button>
        </div>

        {history.surgeries.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No surgical history
          </p>
        ) : (
          <div className="space-y-3">
            {history.surgeries.map((surgery) => (
              <div
                key={surgery.id}
                className={cn(
                  "p-3 rounded-lg border flex items-start gap-3",
                  surgery.isFromPatientRecord && "bg-muted/30"
                )}
              >
                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="md:col-span-2">
                    <Input
                      placeholder="Procedure name"
                      value={surgery.procedure}
                      onChange={(e) =>
                        updateSurgery(surgery.id, "procedure", e.target.value)
                      }
                    />
                  </div>
                  <Input
                    type="date"
                    value={surgery.date || ""}
                    onChange={(e) =>
                      updateSurgery(surgery.id, "date", e.target.value)
                    }
                  />
                </div>
                <button
                  type="button"
                  onClick={() => removeSurgery(surgery.id)}
                  className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-danger shrink-0"
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
            ))}
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <Button type="button" variant="outline" onClick={prevStep}>
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
        <div className="flex gap-2">
          <Button type="button" variant="ghost" onClick={nextStep}>
            Skip
          </Button>
          <Button type="button" onClick={handleContinue} size="lg">
            Continue
            <svg
              className="h-4 w-4 ml-2"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  );
}

export default MedicalHistoryStep;
