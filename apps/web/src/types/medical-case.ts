/**
 * NEURAXIS - Medical Case Types
 * TypeScript types for case creation workflow
 */

// =============================================================================
// Enums
// =============================================================================

export type CaseStatus =
  | "draft"
  | "pending"
  | "in_progress"
  | "completed"
  | "cancelled";
export type UrgencyLevel = "low" | "moderate" | "high" | "critical";
export type SymptomSeverity = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

// =============================================================================
// Step 1: Patient Selection
// =============================================================================

export interface PatientSelection {
  patientId: string;
  mrn: string;
  fullName: string;
  dateOfBirth: string;
  age: number;
  gender: string;
  isNewPatient?: boolean;
}

export interface QuickAddPatient {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: string;
  phonePrimary: string;
  email?: string;
}

// =============================================================================
// Step 2: Chief Complaint
// =============================================================================

export interface ChiefComplaint {
  complaint: string;
  duration: string;
  durationUnit: "hours" | "days" | "weeks" | "months";
  onset: "sudden" | "gradual";
  severity: SymptomSeverity;
  location?: string;
  character?: string;
  aggravatingFactors?: string[];
  relievingFactors?: string[];
}

// =============================================================================
// Step 3: Symptoms
// =============================================================================

export interface Symptom {
  id: string;
  code: string;
  name: string;
  category: string;
  severity: SymptomSeverity;
  duration?: string;
  notes?: string;
  isAISuggested?: boolean;
}

export interface SymptomSearchResult {
  id: string;
  code: string;
  name: string;
  category: string;
  commonSeverity: SymptomSeverity;
  relatedSymptoms: string[];
}

export interface SymptomCategory {
  id: string;
  name: string;
  symptoms: SymptomSearchResult[];
}

// =============================================================================
// Step 4: Vital Signs
// =============================================================================

export interface VitalSigns {
  bloodPressureSystolic: number;
  bloodPressureDiastolic: number;
  heartRate: number;
  temperature: number;
  temperatureUnit: "F" | "C";
  oxygenSaturation: number;
  respiratoryRate: number;
  weight?: number;
  weightUnit?: "kg" | "lbs";
  height?: number;
  heightUnit?: "cm" | "in";
  painLevel?: SymptomSeverity;
  recordedAt: string;
}

export interface VitalNormalRange {
  min: number;
  max: number;
  unit: string;
}

export const VITAL_NORMAL_RANGES: Record<string, VitalNormalRange> = {
  bloodPressureSystolic: { min: 90, max: 120, unit: "mmHg" },
  bloodPressureDiastolic: { min: 60, max: 80, unit: "mmHg" },
  heartRate: { min: 60, max: 100, unit: "bpm" },
  temperatureF: { min: 97.8, max: 99.1, unit: "°F" },
  temperatureC: { min: 36.5, max: 37.3, unit: "°C" },
  oxygenSaturation: { min: 95, max: 100, unit: "%" },
  respiratoryRate: { min: 12, max: 20, unit: "/min" },
};

// =============================================================================
// Step 5: Medical History
// =============================================================================

export interface MedicalHistoryItem {
  id: string;
  condition: string;
  diagnosisDate?: string;
  status: "active" | "resolved" | "chronic";
  notes?: string;
  isFromPatientRecord?: boolean;
}

export interface MedicalHistory {
  conditions: MedicalHistoryItem[];
  allergies: Array<{
    id: string;
    allergen: string;
    severity: string;
    reaction: string;
    isFromPatientRecord?: boolean;
  }>;
  surgeries: Array<{
    id: string;
    procedure: string;
    date?: string;
    notes?: string;
    isFromPatientRecord?: boolean;
  }>;
  familyHistory: Array<{
    id: string;
    condition: string;
    relationship: string;
    notes?: string;
    isFromPatientRecord?: boolean;
  }>;
}

// =============================================================================
// Step 6: Current Medications
// =============================================================================

export interface CurrentMedication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  route: string;
  startDate?: string;
  prescribedBy?: string;
  isActive: boolean;
  isFromPatientRecord?: boolean;
  compliance?: "taking" | "not_taking" | "inconsistent";
}

// =============================================================================
// Step 7: Image Upload
// =============================================================================

export interface CaseImage {
  id: string;
  file?: File;
  url?: string;
  thumbnailUrl?: string;
  type: "photo" | "xray" | "scan" | "document" | "other";
  bodyPart?: string;
  description?: string;
  uploadProgress?: number;
  status: "pending" | "uploading" | "uploaded" | "error";
}

// =============================================================================
// Step 8: Assessment Notes
// =============================================================================

export interface AssessmentNotes {
  clinicalImpression: string;
  differentialDiagnosis: string[];
  recommendedTests: string[];
  treatmentPlan?: string;
  followUpInstructions?: string;
  urgencyLevel: UrgencyLevel;
  aiSuggestions?: AISuggestion;
}

// =============================================================================
// AI Assistance
// =============================================================================

export interface AISuggestion {
  relatedSymptoms: Array<{
    symptom: string;
    relevance: number;
    reason: string;
  }>;
  differentialDiagnosis: Array<{
    diagnosis: string;
    probability: number;
    supportingSymptoms: string[];
    suggestedTests: string[];
  }>;
  urgencyAssessment: {
    level: UrgencyLevel;
    reasoning: string;
    redFlags: string[];
  };
  suggestedQuestions: string[];
  confidence: number;
}

export interface AIAnalysisRequest {
  chiefComplaint: ChiefComplaint;
  symptoms: Symptom[];
  vitals: VitalSigns;
  patientAge: number;
  patientGender: string;
  medicalHistory: MedicalHistory;
}

// =============================================================================
// Full Case Form Data
// =============================================================================

export interface CaseFormData {
  // Step tracking
  currentStep: number;
  completedSteps: number[];

  // Step data
  patient: PatientSelection | null;
  chiefComplaint: ChiefComplaint | null;
  symptoms: Symptom[];
  vitals: VitalSigns | null;
  medicalHistory: MedicalHistory | null;
  medications: CurrentMedication[];
  images: CaseImage[];
  assessment: AssessmentNotes | null;

  // Draft management
  draftId?: string;
  lastSavedAt?: string;
  isDirty: boolean;
}

export interface CaseDraft {
  id: string;
  patientId?: string;
  patientName?: string;
  chiefComplaint?: string;
  currentStep: number;
  data: Partial<CaseFormData>;
  createdAt: string;
  updatedAt: string;
}

// =============================================================================
// Case Creation Response
// =============================================================================

export interface CreatedCase {
  id: string;
  caseNumber: string;
  patientId: string;
  status: CaseStatus;
  urgencyLevel: UrgencyLevel;
  createdAt: string;
  createdBy: string;
}

// =============================================================================
// Step Configuration
// =============================================================================

export interface CaseCreationStep {
  id: number;
  key: string;
  title: string;
  description: string;
  isRequired: boolean;
  isComplete: (data: CaseFormData) => boolean;
}

export const CASE_CREATION_STEPS: CaseCreationStep[] = [
  {
    id: 0,
    key: "patient",
    title: "Patient",
    description: "Select or add patient",
    isRequired: true,
    isComplete: (data) => data.patient !== null,
  },
  {
    id: 1,
    key: "complaint",
    title: "Chief Complaint",
    description: "Primary reason for visit",
    isRequired: true,
    isComplete: (data) =>
      data.chiefComplaint !== null && data.chiefComplaint.complaint.length > 0,
  },
  {
    id: 2,
    key: "symptoms",
    title: "Symptoms",
    description: "Related symptoms and severity",
    isRequired: true,
    isComplete: (data) => data.symptoms.length > 0,
  },
  {
    id: 3,
    key: "vitals",
    title: "Vital Signs",
    description: "Current vital measurements",
    isRequired: true,
    isComplete: (data) => data.vitals !== null,
  },
  {
    id: 4,
    key: "history",
    title: "Medical History",
    description: "Review patient history",
    isRequired: false,
    isComplete: (data) => data.medicalHistory !== null,
  },
  {
    id: 5,
    key: "medications",
    title: "Medications",
    description: "Current medications",
    isRequired: false,
    isComplete: () => true, // Optional step
  },
  {
    id: 6,
    key: "images",
    title: "Images",
    description: "Upload relevant images",
    isRequired: false,
    isComplete: () => true, // Optional step
  },
  {
    id: 7,
    key: "assessment",
    title: "Assessment",
    description: "Clinical assessment",
    isRequired: true,
    isComplete: (data) =>
      data.assessment !== null && data.assessment.clinicalImpression.length > 0,
  },
];
