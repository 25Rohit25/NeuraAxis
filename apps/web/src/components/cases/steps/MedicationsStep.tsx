/**
 * NEURAXIS - Medications Step
 * Import and manage current medications from patient profile
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCaseForm } from "@/contexts/CaseFormContext";
import { cn } from "@/lib/utils";
import type { CurrentMedication } from "@/types/medical-case";
import { useEffect, useState } from "react";

const MEDICATION_ROUTES = [
  "Oral",
  "IV",
  "IM",
  "Subcutaneous",
  "Topical",
  "Inhaled",
  "Rectal",
  "Sublingual",
];
const FREQUENCIES = [
  "Once daily",
  "Twice daily",
  "Three times daily",
  "Four times daily",
  "Every 4 hours",
  "Every 6 hours",
  "As needed",
  "At bedtime",
];

export function MedicationsStep() {
  const {
    state,
    setMedications,
    addMedication,
    updateMedication,
    removeMedication,
    nextStep,
    prevStep,
  } = useCaseForm();
  const [isLoading, setIsLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newMed, setNewMed] = useState({
    name: "",
    dosage: "",
    frequency: "Once daily",
    route: "Oral",
  });

  // Fetch from patient record
  useEffect(() => {
    const fetchPatientMedications = async () => {
      if (!state.patient?.patientId || state.medications.length > 0) return;

      setIsLoading(true);
      try {
        const response = await fetch(
          `/api/patients/${state.patient.patientId}/medications`
        );
        if (response.ok) {
          const data = await response.json();
          const meds: CurrentMedication[] = (data.medications || []).map(
            (m: any) => ({
              ...m,
              isFromPatientRecord: true,
              isActive: true,
              compliance: "taking",
            })
          );
          setMedications(meds);
        }
      } catch (error) {
        console.error("Failed to fetch medications:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPatientMedications();
  }, [state.patient, state.medications.length, setMedications]);

  const handleAddMedication = () => {
    if (!newMed.name || !newMed.dosage) return;

    addMedication({
      name: newMed.name,
      dosage: newMed.dosage,
      frequency: newMed.frequency,
      route: newMed.route,
      isActive: true,
      isFromPatientRecord: false,
      compliance: "taking",
    });

    setNewMed({ name: "", dosage: "", frequency: "Once daily", route: "Oral" });
    setShowAddForm(false);
  };

  const getComplianceColor = (compliance: string) => {
    if (compliance === "taking") return "text-success";
    if (compliance === "inconsistent") return "text-warning";
    return "text-danger";
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold mb-1">Current Medications</h2>
          <p className="text-sm text-muted-foreground">
            Loading medications...
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
        <h2 className="text-lg font-semibold mb-1">Current Medications</h2>
        <p className="text-sm text-muted-foreground">
          Review imported medications and update compliance status
        </p>
      </div>

      {/* Medications list */}
      {state.medications.length === 0 && !showAddForm ? (
        <div className="text-center py-8 border rounded-lg border-dashed">
          <svg
            className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
            <path d="m8.5 8.5 7 7" />
          </svg>
          <p className="text-muted-foreground mb-3">No medications on record</p>
          <Button onClick={() => setShowAddForm(true)}>+ Add Medication</Button>
        </div>
      ) : (
        <div className="space-y-3">
          {state.medications.map((med) => (
            <div
              key={med.id}
              className={cn(
                "p-4 rounded-lg border",
                med.isFromPatientRecord ? "bg-muted/30" : "bg-card"
              )}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium">{med.name}</span>
                    {med.isFromPatientRecord && (
                      <span className="text-xs text-muted-foreground px-1.5 py-0.5 rounded bg-muted">
                        From record
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {med.dosage} • {med.frequency} • {med.route}
                  </p>
                </div>

                {/* Compliance selector */}
                <div className="flex items-center gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">
                      Patient Compliance
                    </label>
                    <select
                      value={med.compliance || "taking"}
                      onChange={(e) =>
                        updateMedication(med.id, {
                          compliance: e.target.value as any,
                        })
                      }
                      className={cn(
                        "h-8 px-2 text-sm rounded border bg-background font-medium",
                        getComplianceColor(med.compliance || "taking")
                      )}
                    >
                      <option value="taking">Taking as prescribed</option>
                      <option value="inconsistent">
                        Taking inconsistently
                      </option>
                      <option value="not_taking">Not taking</option>
                    </select>
                  </div>

                  <button
                    type="button"
                    onClick={() => removeMedication(med.id)}
                    className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-danger"
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
            </div>
          ))}

          {/* Add medication button */}
          {!showAddForm && (
            <Button
              variant="outline"
              onClick={() => setShowAddForm(true)}
              className="w-full border-dashed"
            >
              + Add Medication
            </Button>
          )}
        </div>
      )}

      {/* Add medication form */}
      {showAddForm && (
        <div className="p-4 rounded-lg border bg-card">
          <h4 className="font-medium mb-4">Add New Medication</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">
                Medication Name *
              </label>
              <Input
                placeholder="e.g., Lisinopril"
                value={newMed.name}
                onChange={(e) => setNewMed({ ...newMed, name: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">
                Dosage *
              </label>
              <Input
                placeholder="e.g., 10mg"
                value={newMed.dosage}
                onChange={(e) =>
                  setNewMed({ ...newMed, dosage: e.target.value })
                }
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">
                Frequency
              </label>
              <select
                value={newMed.frequency}
                onChange={(e) =>
                  setNewMed({ ...newMed, frequency: e.target.value })
                }
                className="w-full h-10 px-3 rounded-md border bg-background"
              >
                {FREQUENCIES.map((freq) => (
                  <option key={freq} value={freq}>
                    {freq}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-muted-foreground mb-1 block">
                Route
              </label>
              <select
                value={newMed.route}
                onChange={(e) =>
                  setNewMed({ ...newMed, route: e.target.value })
                }
                className="w-full h-10 px-3 rounded-md border bg-background"
              >
                {MEDICATION_ROUTES.map((route) => (
                  <option key={route} value={route}>
                    {route}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowAddForm(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAddMedication}
              disabled={!newMed.name || !newMed.dosage}
            >
              Add Medication
            </Button>
          </div>
        </div>
      )}

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
          <Button type="button" onClick={nextStep} size="lg">
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

export default MedicationsStep;
