/**
 * NEURAXIS - Patient Profile Types
 * TypeScript types for patient profile, timeline, medications, vitals, etc.
 */

// =============================================================================
// Base Types
// =============================================================================

export interface PatientProfile {
  id: string;
  mrn: string;
  firstName: string;
  middleName?: string;
  lastName: string;
  fullName: string;
  dateOfBirth: string;
  age: number;
  gender: "male" | "female" | "other" | "prefer_not_to_say";
  maritalStatus?: string;
  bloodType?: string;
  photoUrl?: string;

  // Contact
  email?: string;
  phonePrimary: string;
  phoneSecondary?: string;

  // Address
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;

  // Emergency Contact
  emergencyContactName: string;
  emergencyContactRelationship: string;
  emergencyContactPhone: string;
  emergencyContactEmail?: string;

  // Insurance
  insuranceProvider?: string;
  insurancePolicyNumber?: string;
  insuranceGroupNumber?: string;
  insuranceDocumentUrl?: string;

  // Status
  status: "active" | "inactive" | "deceased" | "transferred";

  // Audit
  createdAt: string;
  updatedAt: string;
  lastVisitDate?: string;
}

// =============================================================================
// Timeline
// =============================================================================

export type TimelineEventType =
  | "visit"
  | "diagnosis"
  | "procedure"
  | "medication_start"
  | "medication_end"
  | "lab_result"
  | "imaging"
  | "allergy_added"
  | "note"
  | "document";

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description?: string;
  date: string;
  time?: string;
  provider?: {
    id: string;
    name: string;
    specialty?: string;
    photoUrl?: string;
  };
  metadata?: Record<string, any>;
  linkedRecordId?: string;
  linkedRecordType?: string;
}

// =============================================================================
// Medications
// =============================================================================

export type MedicationStatus =
  | "active"
  | "discontinued"
  | "on_hold"
  | "completed";

export interface Medication {
  id: string;
  name: string;
  genericName?: string;
  dosage: string;
  frequency: string;
  route: string; // oral, injection, topical, etc.
  startDate: string;
  endDate?: string;
  prescribedBy: {
    id: string;
    name: string;
  };
  status: MedicationStatus;
  refillsRemaining?: number;
  lastRefillDate?: string;
  nextRefillDate?: string;
  instructions?: string;
  sideEffects?: string[];
  interactions?: string[];
  isControlled?: boolean;
}

// =============================================================================
// Allergies
// =============================================================================

export type AllergySeverity =
  | "mild"
  | "moderate"
  | "severe"
  | "life_threatening";
export type AllergyType = "drug" | "food" | "environmental" | "other";

export interface Allergy {
  id: string;
  allergen: string;
  type: AllergyType;
  severity: AllergySeverity;
  reaction: string;
  onsetDate?: string;
  confirmedBy?: string;
  notes?: string;
}

// =============================================================================
// Chronic Conditions
// =============================================================================

export type ConditionStatus =
  | "active"
  | "resolved"
  | "in_remission"
  | "chronic";

export interface ChronicCondition {
  id: string;
  name: string;
  icdCode?: string;
  diagnosisDate: string;
  status: ConditionStatus;
  severity?: string;
  treatedBy?: {
    id: string;
    name: string;
    specialty: string;
  };
  notes?: string;
  relatedMedications?: string[];
}

// =============================================================================
// Vitals
// =============================================================================

export interface VitalReading {
  id: string;
  date: string;
  time: string;
  type: VitalType;
  value: number;
  unit: string;
  systolic?: number; // for blood pressure
  diastolic?: number; // for blood pressure
  normalRangeMin?: number;
  normalRangeMax?: number;
  isAbnormal?: boolean;
  recordedBy?: string;
  notes?: string;
}

export type VitalType =
  | "blood_pressure"
  | "heart_rate"
  | "temperature"
  | "respiratory_rate"
  | "oxygen_saturation"
  | "weight"
  | "height"
  | "bmi";

export interface VitalTrend {
  type: VitalType;
  label: string;
  unit: string;
  readings: Array<{
    date: string;
    value: number;
    systolic?: number;
    diastolic?: number;
  }>;
  latestValue: number;
  trend: "up" | "down" | "stable";
  isAbnormal: boolean;
}

// =============================================================================
// Lab Results
// =============================================================================

export type LabResultStatus =
  | "normal"
  | "abnormal_low"
  | "abnormal_high"
  | "critical";

export interface LabTest {
  id: string;
  testName: string;
  testCode?: string;
  category: string;
  orderDate: string;
  resultDate?: string;
  status: "pending" | "completed" | "cancelled";
  orderedBy: {
    id: string;
    name: string;
  };
  results: LabResult[];
}

export interface LabResult {
  id: string;
  component: string;
  value: number | string;
  unit: string;
  referenceRange: string;
  status: LabResultStatus;
  flag?: string;
  notes?: string;
}

// =============================================================================
// Medical Images
// =============================================================================

export type ImagingType =
  | "xray"
  | "ct"
  | "mri"
  | "ultrasound"
  | "mammogram"
  | "pet"
  | "other";

export interface MedicalImage {
  id: string;
  type: ImagingType;
  bodyPart: string;
  date: string;
  thumbnailUrl: string;
  fullImageUrl: string;
  dicomUrl?: string;
  orderedBy: {
    id: string;
    name: string;
  };
  radiologistNotes?: string;
  findings?: string;
  impressions?: string;
}

// =============================================================================
// Documents
// =============================================================================

export type DocumentCategory =
  | "insurance"
  | "consent"
  | "lab_report"
  | "imaging_report"
  | "referral"
  | "discharge_summary"
  | "prescription"
  | "other";

export interface PatientDocument {
  id: string;
  name: string;
  category: DocumentCategory;
  fileType: string;
  fileSize: number;
  uploadDate: string;
  uploadedBy: {
    id: string;
    name: string;
  };
  url: string;
  thumbnailUrl?: string;
  description?: string;
  isConfidential?: boolean;
}

// =============================================================================
// Care Team
// =============================================================================

export type CareTeamRole =
  | "primary_care"
  | "specialist"
  | "surgeon"
  | "nurse"
  | "pharmacist"
  | "therapist"
  | "dietitian"
  | "case_manager"
  | "other";

export interface CareTeamMember {
  id: string;
  name: string;
  role: CareTeamRole;
  specialty?: string;
  department?: string;
  photoUrl?: string;
  phone?: string;
  email?: string;
  isPrimary?: boolean;
  assignedDate: string;
  notes?: string;
}

// =============================================================================
// Full Profile Response
// =============================================================================

export interface PatientProfileResponse {
  profile: PatientProfile;
  timeline: TimelineEvent[];
  medications: Medication[];
  allergies: Allergy[];
  conditions: ChronicCondition[];
  vitalTrends: VitalTrend[];
  labResults: LabTest[];
  images: MedicalImage[];
  documents: PatientDocument[];
  careTeam: CareTeamMember[];
  hasEditAccess: boolean;
  lastUpdated: string;
}

// =============================================================================
// Edit Permissions
// =============================================================================

export interface EditPermissions {
  canEditDemographics: boolean;
  canEditMedications: boolean;
  canEditAllergies: boolean;
  canEditConditions: boolean;
  canAddVitals: boolean;
  canUploadDocuments: boolean;
  canAssignCareTeam: boolean;
}
