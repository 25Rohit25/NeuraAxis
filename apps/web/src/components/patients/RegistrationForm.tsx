/**
 * NEURAXIS - Patient Registration Form
 * Multi-step wizard with real-time validation and autocomplete
 */

"use client";

import {
  checkDuplicates,
  getAllergySuggestions,
  getConditionSuggestions,
  getMedicationSuggestions,
  registerPatient,
} from "@/app/actions/patients";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import {
  FileList,
  FileUpload,
  type FileItem,
} from "@/components/ui/FileUpload";
import { Input, TextArea } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { cn } from "@/lib/utils";
import {
  defaultPatientFormData,
  demographicsSchema,
  emergencyContactSchema,
  medicalHistorySchema,
  type DemographicsFormData,
  type EmergencyContactFormData,
  type MedicalHistoryFormData,
  type PatientFormData,
} from "@/lib/validations/patient";
import { zodResolver } from "@hookform/resolvers/zod";
import React, { useCallback, useState, useTransition } from "react";
import { Controller, useForm } from "react-hook-form";

// =============================================================================
// Types
// =============================================================================

interface PotentialDuplicate {
  id: string;
  mrn: string;
  fullName: string;
  dateOfBirth: string;
  similarityScore: number;
  matchReason: string;
}

interface RegistrationFormProps {
  onSuccess?: (result: { id: string; mrn: string }) => void;
  onCancel?: () => void;
}

// =============================================================================
// Step Components
// =============================================================================

// Step indicator component
function StepIndicator({
  currentStep,
  totalSteps,
}: {
  currentStep: number;
  totalSteps: number;
}) {
  const steps = [
    { number: 1, title: "Demographics", description: "Personal information" },
    { number: 2, title: "Medical History", description: "Health conditions" },
    {
      number: 3,
      title: "Emergency Contact",
      description: "Contact & insurance",
    },
  ];

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <React.Fragment key={step.number}>
            {/* Step circle */}
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold transition-all",
                  currentStep > step.number
                    ? "border-success bg-success text-white"
                    : currentStep === step.number
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-muted-foreground/30 bg-background text-muted-foreground"
                )}
              >
                {currentStep > step.number ? (
                  <svg
                    className="h-5 w-5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  step.number
                )}
              </div>
              <div className="mt-2 text-center hidden sm:block">
                <p
                  className={cn(
                    "text-sm font-medium",
                    currentStep >= step.number
                      ? "text-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {step.title}
                </p>
                <p className="text-xs text-muted-foreground">
                  {step.description}
                </p>
              </div>
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "flex-1 h-0.5 mx-4",
                  currentStep > step.number
                    ? "bg-success"
                    : "bg-muted-foreground/30"
                )}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

// Tag input component for arrays (allergies, medications, etc.)
function TagInput({
  value,
  onChange,
  placeholder,
  getSuggestions,
  label,
  error,
}: {
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  getSuggestions?: (query: string) => Promise<string[]>;
  label?: string;
  error?: string;
}) {
  const [inputValue, setInputValue] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);

    if (val.length >= 2 && getSuggestions) {
      const results = await getSuggestions(val);
      setSuggestions(results.filter((s) => !value.includes(s)));
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const addTag = (tag: string) => {
    const trimmed = tag.trim();
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed]);
    }
    setInputValue("");
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const removeTag = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(inputValue);
    }
  };

  return (
    <div className="w-full">
      {label && (
        <label className="mb-1.5 block text-sm font-medium">{label}</label>
      )}

      {/* Tags display */}
      <div className="flex flex-wrap gap-2 mb-2">
        {value.map((tag, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-primary/10 text-primary text-sm"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(index)}
              className="hover:text-primary/70"
              aria-label={`Remove ${tag}`}
            >
              <svg
                className="h-3 w-3"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </span>
        ))}
      </div>

      {/* Input with suggestions */}
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          placeholder={placeholder}
          className={cn(
            "flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm",
            "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
            error ? "border-danger" : "border-input"
          )}
        />

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <ul className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-lg max-h-48 overflow-auto">
            {suggestions.map((suggestion, index) => (
              <li
                key={index}
                onClick={() => addTag(suggestion)}
                className="px-3 py-2 text-sm cursor-pointer hover:bg-muted"
              >
                {suggestion}
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="mt-1 text-xs text-muted-foreground">
        Press Enter or comma to add. Click × to remove.
      </p>
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  );
}

// =============================================================================
// Main Registration Form
// =============================================================================

export function PatientRegistrationForm({
  onSuccess,
  onCancel,
}: RegistrationFormProps) {
  // State
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<PatientFormData>(
    defaultPatientFormData
  );
  const [isPending, startTransition] = useTransition();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<PotentialDuplicate[]>([]);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [insuranceFiles, setInsuranceFiles] = useState<FileItem[]>([]);

  // Step 1 Form
  const step1Form = useForm<DemographicsFormData>({
    resolver: zodResolver(demographicsSchema),
    defaultValues: formData,
    mode: "onBlur",
  });

  // Step 2 Form
  const step2Form = useForm<MedicalHistoryFormData>({
    resolver: zodResolver(medicalHistorySchema),
    defaultValues: formData,
    mode: "onBlur",
  });

  // Step 3 Form
  const step3Form = useForm<EmergencyContactFormData>({
    resolver: zodResolver(emergencyContactSchema),
    defaultValues: formData,
    mode: "onBlur",
  });

  // Gender options
  const genderOptions = [
    { value: "male", label: "Male" },
    { value: "female", label: "Female" },
    { value: "other", label: "Other" },
    { value: "prefer_not_to_say", label: "Prefer not to say" },
  ];

  // Marital status options
  const maritalStatusOptions = [
    { value: "single", label: "Single" },
    { value: "married", label: "Married" },
    { value: "divorced", label: "Divorced" },
    { value: "widowed", label: "Widowed" },
    { value: "separated", label: "Separated" },
    { value: "domestic_partnership", label: "Domestic Partnership" },
  ];

  // Blood type options
  const bloodTypeOptions = [
    { value: "A+", label: "A+" },
    { value: "A-", label: "A-" },
    { value: "B+", label: "B+" },
    { value: "B-", label: "B-" },
    { value: "AB+", label: "AB+" },
    { value: "AB-", label: "AB-" },
    { value: "O+", label: "O+" },
    { value: "O-", label: "O-" },
    { value: "unknown", label: "Unknown" },
  ];

  // US States
  const stateOptions = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
  ].map((s) => ({ value: s, label: s }));

  // Relationship options
  const relationshipOptions = [
    "Spouse",
    "Parent",
    "Child",
    "Sibling",
    "Grandparent",
    "Aunt/Uncle",
    "Cousin",
    "Friend",
    "Partner",
    "Caregiver",
    "Other",
  ].map((r) => ({ value: r, label: r }));

  // Handle step 1 submission
  const handleStep1Submit = async (data: DemographicsFormData) => {
    // Check for duplicates before proceeding
    startTransition(async () => {
      const result = await checkDuplicates(
        data.firstName,
        data.lastName,
        data.dateOfBirth
      );

      if (result.success && result.data?.hasDuplicates) {
        setDuplicates(result.data.potentialDuplicates);
        setShowDuplicateModal(true);
        return;
      }

      // Update form data and proceed
      setFormData((prev) => ({ ...prev, ...data }));
      setCurrentStep(2);
    });
  };

  // Handle step 2 submission
  const handleStep2Submit = (data: MedicalHistoryFormData) => {
    setFormData((prev) => ({ ...prev, ...data }));
    setCurrentStep(3);
  };

  // Handle final submission
  const handleFinalSubmit = async (data: EmergencyContactFormData) => {
    setSubmitError(null);
    const completeData = { ...formData, ...data };

    startTransition(async () => {
      const result = await registerPatient(completeData);

      if (result.success && result.data) {
        onSuccess?.(result.data);
      } else {
        setSubmitError(result.error || "Failed to register patient");
      }
    });
  };

  // Continue despite duplicate warning
  const handleContinueDespiteDuplicate = () => {
    setShowDuplicateModal(false);
    const data = step1Form.getValues();
    setFormData((prev) => ({ ...prev, ...data }));
    setCurrentStep(2);
  };

  // Go back to previous step
  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Autocomplete helpers
  const getMedications = useCallback(async (query: string) => {
    const result = await getMedicationSuggestions(query);
    return result.success ? result.data || [] : [];
  }, []);

  const getConditions = useCallback(async (query: string) => {
    const result = await getConditionSuggestions(query);
    return result.success ? result.data || [] : [];
  }, []);

  const getAllergies = useCallback(async (query: string) => {
    const result = await getAllergySuggestions(query);
    return result.success ? result.data || [] : [];
  }, []);

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Step Indicator */}
      <StepIndicator currentStep={currentStep} totalSteps={3} />

      {/* Error Alert */}
      {submitError && (
        <Alert
          variant="error"
          title="Registration Failed"
          className="mb-6"
          closable
          onClose={() => setSubmitError(null)}
        >
          {submitError}
        </Alert>
      )}

      {/* Step 1: Demographics */}
      {currentStep === 1 && (
        <form
          onSubmit={step1Form.handleSubmit(handleStep1Submit)}
          className="space-y-6"
        >
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Personal Information</h2>

            <div className="grid gap-4 sm:grid-cols-3">
              <Input
                label="First Name"
                required
                {...step1Form.register("firstName")}
                error={step1Form.formState.errors.firstName?.message}
              />
              <Input
                label="Middle Name"
                {...step1Form.register("middleName")}
                error={step1Form.formState.errors.middleName?.message}
              />
              <Input
                label="Last Name"
                required
                {...step1Form.register("lastName")}
                error={step1Form.formState.errors.lastName?.message}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-3 mt-4">
              <Input
                label="Date of Birth"
                type="date"
                required
                {...step1Form.register("dateOfBirth")}
                error={step1Form.formState.errors.dateOfBirth?.message}
              />
              <Controller
                name="gender"
                control={step1Form.control}
                render={({ field }) => (
                  <Select
                    label="Gender"
                    options={genderOptions}
                    value={field.value}
                    onChange={field.onChange}
                    error={step1Form.formState.errors.gender?.message}
                  />
                )}
              />
              <Controller
                name="maritalStatus"
                control={step1Form.control}
                render={({ field }) => (
                  <Select
                    label="Marital Status"
                    options={maritalStatusOptions}
                    value={field.value || ""}
                    onChange={field.onChange}
                    placeholder="Select..."
                  />
                )}
              />
            </div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Contact Information</h2>

            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Email Address"
                type="email"
                {...step1Form.register("email")}
                error={step1Form.formState.errors.email?.message}
              />
              <Input
                label="Primary Phone"
                type="tel"
                required
                placeholder="(555) 123-4567"
                {...step1Form.register("phonePrimary")}
                error={step1Form.formState.errors.phonePrimary?.message}
              />
            </div>

            <Input
              label="Secondary Phone"
              type="tel"
              className="mt-4"
              placeholder="(555) 123-4567"
              {...step1Form.register("phoneSecondary")}
              error={step1Form.formState.errors.phoneSecondary?.message}
            />
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Address</h2>

            <Input
              label="Address Line 1"
              required
              {...step1Form.register("addressLine1")}
              error={step1Form.formState.errors.addressLine1?.message}
            />
            <Input
              label="Address Line 2"
              className="mt-4"
              placeholder="Apt, Suite, Unit, etc."
              {...step1Form.register("addressLine2")}
            />

            <div className="grid gap-4 sm:grid-cols-3 mt-4">
              <Input
                label="City"
                required
                {...step1Form.register("city")}
                error={step1Form.formState.errors.city?.message}
              />
              <Controller
                name="state"
                control={step1Form.control}
                render={({ field }) => (
                  <Select
                    label="State"
                    options={stateOptions}
                    value={field.value}
                    onChange={field.onChange}
                    searchable
                    error={step1Form.formState.errors.state?.message}
                  />
                )}
              />
              <Input
                label="Postal Code"
                required
                {...step1Form.register("postalCode")}
                error={step1Form.formState.errors.postalCode?.message}
              />
            </div>
          </div>

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button type="button" variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isPending}>
              Next: Medical History
            </Button>
          </div>
        </form>
      )}

      {/* Step 2: Medical History */}
      {currentStep === 2 && (
        <form
          onSubmit={step2Form.handleSubmit(handleStep2Submit)}
          className="space-y-6"
        >
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Basic Measurements</h2>

            <div className="grid gap-4 sm:grid-cols-3">
              <Controller
                name="bloodType"
                control={step2Form.control}
                render={({ field }) => (
                  <Select
                    label="Blood Type"
                    options={bloodTypeOptions}
                    value={field.value || ""}
                    onChange={field.onChange}
                    placeholder="Select..."
                  />
                )}
              />
              <Input
                label="Height (cm)"
                type="number"
                {...step2Form.register("heightCm", { valueAsNumber: true })}
                error={step2Form.formState.errors.heightCm?.message}
              />
              <Input
                label="Weight (kg)"
                type="number"
                {...step2Form.register("weightKg", { valueAsNumber: true })}
                error={step2Form.formState.errors.weightKg?.message}
              />
            </div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">
              Allergies & Conditions
            </h2>

            <Controller
              name="allergies"
              control={step2Form.control}
              render={({ field }) => (
                <TagInput
                  label="Known Allergies"
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="Type allergy and press Enter..."
                  getSuggestions={getAllergies}
                />
              )}
            />

            <div className="mt-4">
              <Controller
                name="chronicConditions"
                control={step2Form.control}
                render={({ field }) => (
                  <TagInput
                    label="Chronic Conditions"
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Type condition and press Enter..."
                    getSuggestions={getConditions}
                  />
                )}
              />
            </div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">
              Medications & Procedures
            </h2>

            <Controller
              name="currentMedications"
              control={step2Form.control}
              render={({ field }) => (
                <TagInput
                  label="Current Medications"
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="Type medication and press Enter..."
                  getSuggestions={getMedications}
                />
              )}
            />

            <div className="mt-4">
              <Controller
                name="pastSurgeries"
                control={step2Form.control}
                render={({ field }) => (
                  <TagInput
                    label="Past Surgeries"
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Type surgery and press Enter..."
                  />
                )}
              />
            </div>

            <div className="mt-4">
              <Controller
                name="familyHistory"
                control={step2Form.control}
                render={({ field }) => (
                  <TextArea
                    label="Family Medical History"
                    placeholder="Note any significant family medical history..."
                    rows={4}
                    {...field}
                    value={field.value || ""}
                    error={step2Form.formState.errors.familyHistory?.message}
                  />
                )}
              />
            </div>
          </div>

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button type="button" variant="outline" onClick={handleBack}>
              Back
            </Button>
            <Button type="submit">Next: Emergency Contact</Button>
          </div>
        </form>
      )}

      {/* Step 3: Emergency Contact */}
      {currentStep === 3 && (
        <form
          onSubmit={step3Form.handleSubmit(handleFinalSubmit)}
          className="space-y-6"
        >
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Emergency Contact</h2>

            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Contact Name"
                required
                {...step3Form.register("emergencyContactName")}
                error={step3Form.formState.errors.emergencyContactName?.message}
              />
              <Controller
                name="emergencyContactRelationship"
                control={step3Form.control}
                render={({ field }) => (
                  <Select
                    label="Relationship"
                    options={relationshipOptions}
                    value={field.value}
                    onChange={field.onChange}
                    error={
                      step3Form.formState.errors.emergencyContactRelationship
                        ?.message
                    }
                  />
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2 mt-4">
              <Input
                label="Phone Number"
                type="tel"
                required
                placeholder="(555) 123-4567"
                {...step3Form.register("emergencyContactPhone")}
                error={
                  step3Form.formState.errors.emergencyContactPhone?.message
                }
              />
              <Input
                label="Email Address"
                type="email"
                {...step3Form.register("emergencyContactEmail")}
                error={
                  step3Form.formState.errors.emergencyContactEmail?.message
                }
              />
            </div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">
              Insurance Information
            </h2>

            <div className="grid gap-4 sm:grid-cols-2">
              <Input
                label="Insurance Provider"
                {...step3Form.register("insuranceProvider")}
              />
              <Input
                label="Policy Number"
                {...step3Form.register("insurancePolicyNumber")}
              />
            </div>

            <Input
              label="Group Number"
              className="mt-4"
              {...step3Form.register("insuranceGroupNumber")}
            />

            <div className="mt-4">
              <FileUpload
                label="Insurance Card (optional)"
                accept=".pdf,.jpg,.jpeg,.png"
                maxSize={10 * 1024 * 1024}
                hint="Upload a photo or PDF of your insurance card"
                onFilesSelected={(files) => {
                  setInsuranceFiles(files.map((f) => ({ file: f })));
                }}
              />
              {insuranceFiles.length > 0 && (
                <FileList
                  files={insuranceFiles}
                  onRemove={(index) =>
                    setInsuranceFiles((prev) =>
                      prev.filter((_, i) => i !== index)
                    )
                  }
                  className="mt-2"
                />
              )}
            </div>
          </div>

          {/* Summary */}
          <div className="rounded-lg border bg-muted/50 p-6">
            <h2 className="text-lg font-semibold mb-4">Registration Summary</h2>
            <dl className="grid gap-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Patient Name</dt>
                <dd className="font-medium">
                  {formData.firstName} {formData.lastName}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Date of Birth</dt>
                <dd className="font-medium">{formData.dateOfBirth}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Phone</dt>
                <dd className="font-medium">{formData.phonePrimary}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Address</dt>
                <dd className="font-medium">
                  {formData.city}, {formData.state}
                </dd>
              </div>
              {formData.allergies.length > 0 && (
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Allergies</dt>
                  <dd className="font-medium text-danger">
                    {formData.allergies.join(", ")}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button type="button" variant="outline" onClick={handleBack}>
              Back
            </Button>
            <Button type="submit" isLoading={isPending}>
              Complete Registration
            </Button>
          </div>
        </form>
      )}

      {/* Duplicate Warning Modal */}
      <Modal
        isOpen={showDuplicateModal}
        onClose={() => setShowDuplicateModal(false)}
        title="Potential Duplicate Found"
        size="lg"
      >
        <Alert variant="warning" className="mb-4">
          We found existing patient records that may match this patient. Please
          review before continuing.
        </Alert>

        <div className="space-y-3 mb-6">
          {duplicates.map((dup) => (
            <div
              key={dup.id}
              className="flex items-center justify-between p-3 rounded-lg border bg-muted/50"
            >
              <div>
                <p className="font-medium">{dup.fullName}</p>
                <p className="text-sm text-muted-foreground">
                  MRN: {dup.mrn} | DOB: {dup.dateOfBirth}
                </p>
                <p className="text-xs text-muted-foreground">
                  {dup.matchReason}
                </p>
              </div>
              <div className="text-right">
                <span
                  className={cn(
                    "inline-flex px-2 py-1 rounded-full text-xs font-medium",
                    dup.similarityScore >= 0.9
                      ? "bg-danger/10 text-danger"
                      : dup.similarityScore >= 0.7
                        ? "bg-warning/10 text-warning"
                        : "bg-muted text-muted-foreground"
                  )}
                >
                  {Math.round(dup.similarityScore * 100)}% match
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={() => setShowDuplicateModal(false)}
          >
            Edit Information
          </Button>
          <Button variant="warning" onClick={handleContinueDespiteDuplicate}>
            Continue Anyway
          </Button>
        </div>
      </Modal>
    </div>
  );
}

export default PatientRegistrationForm;
