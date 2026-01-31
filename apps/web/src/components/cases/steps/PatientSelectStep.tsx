/**
 * NEURAXIS - Patient Selection Step
 * Search and select or quick-add a patient
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { useCaseForm } from "@/contexts/CaseFormContext";
import { debounce, formatDate } from "@/lib/utils";
import {
  quickAddPatientSchema,
  type QuickAddPatientInput,
} from "@/lib/validations/case";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";

interface PatientSearchResult {
  id: string;
  mrn: string;
  firstName: string;
  lastName: string;
  fullName: string;
  dateOfBirth: string;
  age: number;
  gender: string;
  phonePrimary: string;
  lastVisit?: string;
}

export function PatientSelectStep() {
  const { state, setPatient, nextStep } = useCaseForm();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<PatientSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [selectedPatient, setSelectedPatient] =
    useState<PatientSearchResult | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Quick add form
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<QuickAddPatientInput>({
    resolver: zodResolver(quickAddPatientSchema),
  });

  // Focus search on mount
  useEffect(() => {
    searchInputRef.current?.focus();
  }, []);

  // Search patients
  const searchPatients = useCallback(
    debounce(async (query: string) => {
      if (query.length < 2) {
        setSearchResults([]);
        return;
      }

      setIsSearching(true);
      try {
        const response = await fetch(
          `/api/patients/search?q=${encodeURIComponent(query)}&limit=10`
        );
        if (response.ok) {
          const data = await response.json();
          setSearchResults(data.patients || []);
        }
      } catch (error) {
        console.error("Patient search error:", error);
      } finally {
        setIsSearching(false);
      }
    }, 300),
    []
  );

  useEffect(() => {
    searchPatients(searchQuery);
  }, [searchQuery, searchPatients]);

  const handleSelectPatient = (patient: PatientSearchResult) => {
    setSelectedPatient(patient);
    setPatient({
      patientId: patient.id,
      mrn: patient.mrn,
      fullName: patient.fullName,
      dateOfBirth: patient.dateOfBirth,
      age: patient.age,
      gender: patient.gender,
      isNewPatient: false,
    });
  };

  const handleQuickAdd = async (data: QuickAddPatientInput) => {
    try {
      // Transform camelCase to snake_case for backend
      const payload = {
        first_name: data.firstName,
        last_name: data.lastName,
        date_of_birth: data.dateOfBirth,
        gender: data.gender,
        phone: data.phonePrimary,
        email: data.email || null,
      };

      const response = await fetch("/api/patients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("API Error:", errorData);
        throw new Error("Failed to create patient");
      }

      const newPatient = await response.json();

      const age = Math.floor(
        (Date.now() - new Date(data.dateOfBirth).getTime()) /
          (365.25 * 24 * 60 * 60 * 1000)
      );

      setPatient({
        patientId: newPatient.id,
        mrn: newPatient.medical_record_number || `MRN-${Date.now()}`,
        fullName: `${data.firstName} ${data.lastName}`,
        dateOfBirth: data.dateOfBirth,
        age,
        gender: data.gender,
        isNewPatient: true,
      });

      setShowQuickAdd(false);
      reset();
    } catch (error) {
      console.error("Quick add error:", error);
    }
  };

  const handleContinue = () => {
    if (state.patient) {
      nextStep();
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Select Patient</h2>
        <p className="text-sm text-muted-foreground">
          Search for an existing patient or quickly add a new one
        </p>
      </div>

      {/* Selected patient card */}
      {state.patient && (
        <div className="p-4 rounded-lg border-2 border-primary bg-primary/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-lg">
                {state.patient.fullName
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .slice(0, 2)}
              </div>
              <div>
                <p className="font-medium">{state.patient.fullName}</p>
                <p className="text-sm text-muted-foreground">
                  MRN: {state.patient.mrn} • {state.patient.age} yrs •{" "}
                  {state.patient.gender}
                </p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setPatient(null)}>
              Change
            </Button>
          </div>
        </div>
      )}

      {!state.patient && (
        <>
          {/* Search input */}
          <div className="relative">
            <div className="relative">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.3-4.3" />
              </svg>
              <Input
                ref={searchInputRef}
                type="search"
                placeholder="Search by name, MRN, DOB, or phone..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-12 text-lg"
              />
              {isSearching && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full" />
                </div>
              )}
            </div>
          </div>

          {/* Search results */}
          {searchResults.length > 0 && (
            <div className="border rounded-lg divide-y max-h-80 overflow-y-auto">
              {searchResults.map((patient) => (
                <button
                  key={patient.id}
                  onClick={() => handleSelectPatient(patient)}
                  className="w-full flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors text-left"
                >
                  <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center font-medium text-sm">
                    {patient.firstName[0]}
                    {patient.lastName[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{patient.fullName}</p>
                    <p className="text-sm text-muted-foreground">
                      MRN: {patient.mrn} • {patient.age} yrs • {patient.gender}
                    </p>
                  </div>
                  <div className="text-right text-sm text-muted-foreground shrink-0">
                    <p>DOB: {formatDate(patient.dateOfBirth)}</p>
                    {patient.lastVisit && (
                      <p>Last visit: {formatDate(patient.lastVisit)}</p>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* No results */}
          {searchQuery.length >= 2 &&
            !isSearching &&
            searchResults.length === 0 && (
              <div className="text-center py-8 border rounded-lg">
                <svg
                  className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                >
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.3-4.3" />
                </svg>
                <p className="text-muted-foreground mb-3">No patients found</p>
                <Button onClick={() => setShowQuickAdd(true)}>
                  Quick Add New Patient
                </Button>
              </div>
            )}

          {/* Quick add button */}
          {searchQuery.length < 2 && (
            <div className="text-center py-6 border rounded-lg border-dashed">
              <p className="text-muted-foreground mb-3">
                Can't find the patient?
              </p>
              <Button variant="outline" onClick={() => setShowQuickAdd(true)}>
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
                Quick Add New Patient
              </Button>
            </div>
          )}
        </>
      )}

      {/* Continue button */}
      <div className="flex justify-end">
        <Button onClick={handleContinue} disabled={!state.patient} size="lg">
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

      {/* Quick Add Modal */}
      <Modal
        isOpen={showQuickAdd}
        onClose={() => setShowQuickAdd(false)}
        title="Quick Add Patient"
        size="md"
      >
        <form onSubmit={handleSubmit(handleQuickAdd)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-1.5 block">
                First Name *
              </label>
              <Input {...register("firstName")} placeholder="First name" />
              {errors.firstName && (
                <p className="text-xs text-danger mt-1">
                  {errors.firstName.message}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">
                Last Name *
              </label>
              <Input {...register("lastName")} placeholder="Last name" />
              {errors.lastName && (
                <p className="text-xs text-danger mt-1">
                  {errors.lastName.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-1.5 block">
                Date of Birth *
              </label>
              <Input type="date" {...register("dateOfBirth")} />
              {errors.dateOfBirth && (
                <p className="text-xs text-danger mt-1">
                  {errors.dateOfBirth.message}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">
                Gender *
              </label>
              <select
                {...register("gender")}
                className="w-full h-10 px-3 rounded-md border bg-background"
              >
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
              {errors.gender && (
                <p className="text-xs text-danger mt-1">
                  {errors.gender.message}
                </p>
              )}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-1.5 block">Phone *</label>
            <Input
              {...register("phonePrimary")}
              placeholder="Phone number"
              type="tel"
            />
            {errors.phonePrimary && (
              <p className="text-xs text-danger mt-1">
                {errors.phonePrimary.message}
              </p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium mb-1.5 block">
              Email (optional)
            </label>
            <Input {...register("email")} placeholder="Email" type="email" />
            {errors.email && (
              <p className="text-xs text-danger mt-1">{errors.email.message}</p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowQuickAdd(false)}
            >
              Cancel
            </Button>
            <Button type="submit" isLoading={isSubmitting}>
              Add & Select Patient
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default PatientSelectStep;
