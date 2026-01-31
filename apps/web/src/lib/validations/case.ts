/**
 * NEURAXIS - Medical Case Validation Schemas
 * Zod schemas for case creation form validation
 */

import { z } from "zod";

// =============================================================================
// Common Schemas
// =============================================================================

export const severitySchema = z.number().int().min(1).max(10);

// =============================================================================
// Step 1: Patient Selection
// =============================================================================

export const patientSelectionSchema = z.object({
  patientId: z.string().uuid("Invalid patient ID"),
  mrn: z.string().min(1, "MRN is required"),
  fullName: z.string().min(1, "Patient name is required"),
  dateOfBirth: z.string().min(1, "Date of birth is required"),
  age: z.number().int().min(0).max(150),
  gender: z.string().min(1, "Gender is required"),
  isNewPatient: z.boolean().optional(),
});

export const quickAddPatientSchema = z.object({
  firstName: z.string().min(1, "First name is required").max(50),
  lastName: z.string().min(1, "Last name is required").max(50),
  dateOfBirth: z.string().refine((date) => {
    const parsed = new Date(date);
    return !isNaN(parsed.getTime()) && parsed < new Date();
  }, "Invalid date of birth"),
  gender: z.enum(["male", "female", "other", "prefer_not_to_say"], {
    required_error: "Gender is required",
  }),
  phonePrimary: z.string().min(10, "Valid phone number is required"),
  email: z.string().email().optional().or(z.literal("")),
});

// =============================================================================
// Step 2: Chief Complaint
// =============================================================================

export const chiefComplaintSchema = z.object({
  complaint: z
    .string()
    .min(5, "Please describe the complaint in more detail")
    .max(500, "Complaint too long"),
  duration: z.string().min(1, "Duration is required"),
  durationUnit: z.enum(["hours", "days", "weeks", "months"]),
  onset: z.enum(["sudden", "gradual"]),
  severity: severitySchema,
  location: z.string().max(100).optional(),
  character: z.string().max(200).optional(),
  aggravatingFactors: z.array(z.string().max(100)).optional(),
  relievingFactors: z.array(z.string().max(100)).optional(),
});

// =============================================================================
// Step 3: Symptoms
// =============================================================================

export const symptomSchema = z.object({
  id: z.string(),
  code: z.string(),
  name: z.string().min(1, "Symptom name is required"),
  category: z.string(),
  severity: severitySchema,
  duration: z.string().optional(),
  notes: z.string().max(500).optional(),
  isAISuggested: z.boolean().optional(),
});

export const symptomsSchema = z
  .array(symptomSchema)
  .min(1, "At least one symptom is required");

// =============================================================================
// Step 4: Vital Signs
// =============================================================================

export const vitalSignsSchema = z
  .object({
    bloodPressureSystolic: z
      .number()
      .min(50, "Systolic BP too low")
      .max(250, "Systolic BP too high"),
    bloodPressureDiastolic: z
      .number()
      .min(30, "Diastolic BP too low")
      .max(150, "Diastolic BP too high"),
    heartRate: z
      .number()
      .min(20, "Heart rate too low")
      .max(250, "Heart rate too high"),
    temperature: z
      .number()
      .min(90, "Temperature too low")
      .max(110, "Temperature too high"),
    temperatureUnit: z.enum(["F", "C"]),
    oxygenSaturation: z
      .number()
      .min(0, "Invalid O2 saturation")
      .max(100, "O2 saturation cannot exceed 100%"),
    respiratoryRate: z
      .number()
      .min(5, "Respiratory rate too low")
      .max(60, "Respiratory rate too high"),
    weight: z.number().min(0).max(500).optional(),
    weightUnit: z.enum(["kg", "lbs"]).optional(),
    height: z.number().min(0).max(300).optional(),
    heightUnit: z.enum(["cm", "in"]).optional(),
    painLevel: severitySchema.optional(),
    recordedAt: z.string(),
  })
  .refine(
    (data) => {
      return data.bloodPressureSystolic > data.bloodPressureDiastolic;
    },
    {
      message: "Systolic BP must be greater than diastolic BP",
      path: ["bloodPressureSystolic"],
    }
  );

// =============================================================================
// Step 5: Medical History
// =============================================================================

export const medicalHistoryItemSchema = z.object({
  id: z.string(),
  condition: z.string().min(1, "Condition name is required"),
  diagnosisDate: z.string().optional(),
  status: z.enum(["active", "resolved", "chronic"]),
  notes: z.string().max(500).optional(),
  isFromPatientRecord: z.boolean().optional(),
});

export const allergySchema = z.object({
  id: z.string(),
  allergen: z.string().min(1, "Allergen is required"),
  severity: z.string(),
  reaction: z.string().min(1, "Reaction is required"),
  isFromPatientRecord: z.boolean().optional(),
});

export const surgerySchema = z.object({
  id: z.string(),
  procedure: z.string().min(1, "Procedure name is required"),
  date: z.string().optional(),
  notes: z.string().max(500).optional(),
  isFromPatientRecord: z.boolean().optional(),
});

export const familyHistorySchema = z.object({
  id: z.string(),
  condition: z.string().min(1, "Condition is required"),
  relationship: z.string().min(1, "Relationship is required"),
  notes: z.string().max(500).optional(),
  isFromPatientRecord: z.boolean().optional(),
});

export const medicalHistorySchema = z.object({
  conditions: z.array(medicalHistoryItemSchema),
  allergies: z.array(allergySchema),
  surgeries: z.array(surgerySchema),
  familyHistory: z.array(familyHistorySchema),
});

// =============================================================================
// Step 6: Current Medications
// =============================================================================

export const currentMedicationSchema = z.object({
  id: z.string(),
  name: z.string().min(1, "Medication name is required"),
  dosage: z.string().min(1, "Dosage is required"),
  frequency: z.string().min(1, "Frequency is required"),
  route: z.string().min(1, "Route is required"),
  startDate: z.string().optional(),
  prescribedBy: z.string().optional(),
  isActive: z.boolean(),
  isFromPatientRecord: z.boolean().optional(),
  compliance: z.enum(["taking", "not_taking", "inconsistent"]).optional(),
});

export const medicationsSchema = z.array(currentMedicationSchema);

// =============================================================================
// Step 7: Image Upload
// =============================================================================

export const caseImageSchema = z.object({
  id: z.string(),
  url: z.string().optional(),
  thumbnailUrl: z.string().optional(),
  type: z.enum(["photo", "xray", "scan", "document", "other"]),
  bodyPart: z.string().optional(),
  description: z.string().max(200).optional(),
  status: z.enum(["pending", "uploading", "uploaded", "error"]),
});

export const imagesSchema = z.array(caseImageSchema);

// =============================================================================
// Step 8: Assessment Notes
// =============================================================================

export const assessmentNotesSchema = z.object({
  clinicalImpression: z
    .string()
    .min(10, "Clinical impression is too short")
    .max(2000, "Clinical impression is too long"),
  differentialDiagnosis: z
    .array(z.string().min(1))
    .min(1, "At least one differential diagnosis is required"),
  recommendedTests: z.array(z.string()),
  treatmentPlan: z.string().max(2000).optional(),
  followUpInstructions: z.string().max(1000).optional(),
  urgencyLevel: z.enum(["low", "moderate", "high", "critical"]),
});

// =============================================================================
// Full Case Form Schema
// =============================================================================

export const caseFormSchema = z.object({
  patient: patientSelectionSchema,
  chiefComplaint: chiefComplaintSchema,
  symptoms: symptomsSchema,
  vitals: vitalSignsSchema,
  medicalHistory: medicalHistorySchema.optional(),
  medications: medicationsSchema.optional(),
  images: imagesSchema.optional(),
  assessment: assessmentNotesSchema,
});

// =============================================================================
// Type Exports
// =============================================================================

export type PatientSelectionInput = z.infer<typeof patientSelectionSchema>;
export type QuickAddPatientInput = z.infer<typeof quickAddPatientSchema>;
export type ChiefComplaintInput = z.infer<typeof chiefComplaintSchema>;
export type SymptomInput = z.infer<typeof symptomSchema>;
export type VitalSignsInput = z.infer<typeof vitalSignsSchema>;
export type MedicalHistoryInput = z.infer<typeof medicalHistorySchema>;
export type CurrentMedicationInput = z.infer<typeof currentMedicationSchema>;
export type CaseImageInput = z.infer<typeof caseImageSchema>;
export type AssessmentNotesInput = z.infer<typeof assessmentNotesSchema>;
export type CaseFormInput = z.infer<typeof caseFormSchema>;
