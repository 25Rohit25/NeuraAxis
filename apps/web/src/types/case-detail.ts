/**
 * NEURAXIS - Case Detail Types
 * TypeScript types for case detail view and collaboration
 */

// =============================================================================
// Case Detail Types
// =============================================================================

export interface CaseDetail {
  id: string;
  caseNumber: string;
  status: CaseStatus;
  priority: CasePriority;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;

  // Patient
  patient: PatientDetail;

  // Medical data
  chiefComplaint: ChiefComplaintDetail;
  symptoms: SymptomDetail[];
  vitals: VitalsDetail;
  medicalHistory: MedicalHistoryDetail;
  medications: MedicationDetail[];
  images: CaseImageDetail[];
  labResults: LabResultDetail[];

  // Clinical
  clinicalNotes: ClinicalNote[];
  treatmentPlan: TreatmentPlan;
  aiAnalysis: AIAnalysisResult;

  // Assignment
  assignedTo: DoctorDetail;
  createdBy: DoctorDetail;
  careTeam: DoctorDetail[];

  // Collaboration
  timeline: TimelineEvent[];
  comments: CommentThread[];
  documents: CaseDocument[];

  // Metadata
  version: number;
  lastEditedBy?: DoctorDetail;
  isLocked?: boolean;
  lockedBy?: DoctorDetail;
}

export type CaseStatus =
  | "draft"
  | "pending"
  | "in_progress"
  | "review"
  | "completed"
  | "archived";
export type CasePriority = "low" | "moderate" | "high" | "critical";

// =============================================================================
// Patient & Doctor Types
// =============================================================================

export interface PatientDetail {
  id: string;
  mrn: string;
  firstName: string;
  lastName: string;
  fullName: string;
  dateOfBirth: string;
  age: number;
  gender: string;
  bloodType?: string;
  avatarUrl?: string;
  contactPhone: string;
  contactEmail?: string;
  emergencyContact?: {
    name: string;
    relationship: string;
    phone: string;
  };
  insuranceInfo?: {
    provider: string;
    policyNumber: string;
  };
}

export interface DoctorDetail {
  id: string;
  firstName: string;
  lastName: string;
  fullName: string;
  specialty: string;
  title: string;
  avatarUrl?: string;
  email: string;
  department?: string;
}

// =============================================================================
// Medical Data Types
// =============================================================================

export interface ChiefComplaintDetail {
  complaint: string;
  duration: string;
  durationUnit: string;
  onset: string;
  severity: number;
  location?: string;
  character?: string;
  aggravatingFactors: string[];
  relievingFactors: string[];
  associatedSymptoms: string[];
}

export interface SymptomDetail {
  id: string;
  code: string;
  name: string;
  category: string;
  severity: number;
  duration?: string;
  notes?: string;
  isAISuggested?: boolean;
  addedAt: string;
}

export interface VitalsDetail {
  id: string;
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
  painLevel?: number;
  recordedAt: string;
  recordedBy: DoctorDetail;
}

export interface MedicalHistoryDetail {
  conditions: Array<{
    id: string;
    condition: string;
    diagnosisDate?: string;
    status: "active" | "resolved" | "chronic";
    notes?: string;
    icdCode?: string;
  }>;
  allergies: Array<{
    id: string;
    allergen: string;
    severity: "mild" | "moderate" | "severe" | "life-threatening";
    reaction: string;
    verifiedAt?: string;
  }>;
  surgeries: Array<{
    id: string;
    procedure: string;
    date?: string;
    notes?: string;
    cptCode?: string;
  }>;
  familyHistory: Array<{
    id: string;
    condition: string;
    relationship: string;
    notes?: string;
  }>;
}

export interface MedicationDetail {
  id: string;
  name: string;
  genericName?: string;
  dosage: string;
  frequency: string;
  route: string;
  startDate?: string;
  endDate?: string;
  prescribedBy?: DoctorDetail;
  isActive: boolean;
  compliance?: "taking" | "not_taking" | "inconsistent";
  notes?: string;
  rxNormCode?: string;
}

// =============================================================================
// Image & Lab Types
// =============================================================================

export interface CaseImageDetail {
  id: string;
  url: string;
  thumbnailUrl: string;
  type: "photo" | "xray" | "ct" | "mri" | "ultrasound" | "document" | "other";
  bodyPart?: string;
  description?: string;
  uploadedAt: string;
  uploadedBy: DoctorDetail;
  aiAnnotations?: AIAnnotation[];
  findings?: string;
}

export interface AIAnnotation {
  id: string;
  type: "region" | "measurement" | "finding";
  coordinates: { x: number; y: number; width?: number; height?: number };
  label: string;
  confidence: number;
  description?: string;
}

export interface LabResultDetail {
  id: string;
  testName: string;
  category: string;
  value: string | number;
  unit: string;
  normalRange: { min: number; max: number };
  status: "normal" | "low" | "high" | "critical";
  orderedAt: string;
  resultedAt?: string;
  orderedBy: DoctorDetail;
  loincCode?: string;
  notes?: string;
}

// =============================================================================
// Clinical Notes Types
// =============================================================================

export interface ClinicalNote {
  id: string;
  type: "progress" | "procedure" | "consultation" | "discharge" | "other";
  title: string;
  content: string; // Rich text HTML/JSON
  createdAt: string;
  updatedAt: string;
  author: DoctorDetail;
  coAuthors?: DoctorDetail[];
  isLocked: boolean;
  version: number;
  signedAt?: string;
  signedBy?: DoctorDetail;
  template?: string;
  attachments?: string[];
}

export interface NoteTemplate {
  id: string;
  name: string;
  type: ClinicalNote["type"];
  content: string;
  variables: string[];
  createdBy: string;
  isDefault: boolean;
}

// =============================================================================
// Treatment Plan Types
// =============================================================================

export interface TreatmentPlan {
  id: string;
  diagnosis: Diagnosis[];
  medications: PrescribedMedication[];
  procedures: PlannedProcedure[];
  followUp: FollowUpPlan;
  restrictions: string[];
  goals: TreatmentGoal[];
  instructions: string;
  updatedAt: string;
  updatedBy: DoctorDetail;
}

export interface Diagnosis {
  id: string;
  code: string; // ICD-10
  description: string;
  type: "primary" | "secondary" | "differential";
  status: "confirmed" | "provisional" | "ruled-out";
  confirmedAt?: string;
  confirmedBy?: DoctorDetail;
}

export interface PrescribedMedication {
  id: string;
  medication: string;
  dosage: string;
  frequency: string;
  route: string;
  duration: string;
  instructions: string;
  refills?: number;
  prescribedAt: string;
  prescribedBy: DoctorDetail;
}

export interface PlannedProcedure {
  id: string;
  name: string;
  cptCode?: string;
  scheduledDate?: string;
  priority: "routine" | "urgent" | "emergent";
  notes?: string;
  status: "planned" | "scheduled" | "completed" | "cancelled";
}

export interface FollowUpPlan {
  scheduledDate?: string;
  interval?: string;
  reason: string;
  instructions?: string;
  appointmentId?: string;
}

export interface TreatmentGoal {
  id: string;
  description: string;
  targetDate?: string;
  status: "pending" | "in_progress" | "achieved" | "not_achieved";
  metrics?: string;
}

// =============================================================================
// AI Analysis Types
// =============================================================================

export interface AIAnalysisResult {
  id: string;
  analyzedAt: string;
  modelVersion: string;
  confidence: number;
  differentialDiagnosis: Array<{
    diagnosis: string;
    icdCode?: string;
    probability: number;
    supportingEvidence: string[];
    suggestedTests: string[];
    reasoning: string;
  }>;
  urgencyAssessment: {
    level: "low" | "moderate" | "high" | "critical";
    reasoning: string;
    redFlags: string[];
    recommendedActions: string[];
  };
  suggestedQuestions: string[];
  relatedConditions: string[];
  clinicalGuidelines: Array<{
    source: string;
    recommendation: string;
    evidenceLevel: string;
  }>;
  disclaimer: string;
}

// =============================================================================
// Timeline & Activity Types
// =============================================================================

export interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description?: string;
  timestamp: string;
  actor: DoctorDetail;
  metadata?: Record<string, any>;
  relatedEntityId?: string;
  relatedEntityType?: string;
}

export type TimelineEventType =
  | "case_created"
  | "case_updated"
  | "status_changed"
  | "priority_changed"
  | "assigned"
  | "note_added"
  | "note_updated"
  | "vital_recorded"
  | "image_uploaded"
  | "lab_result_added"
  | "treatment_updated"
  | "comment_added"
  | "document_generated"
  | "ai_analysis_run";

// =============================================================================
// Collaboration Types
// =============================================================================

export interface CommentThread {
  id: string;
  sectionId: string; // Which section this comment is on
  sectionType: "note" | "diagnosis" | "treatment" | "image" | "general";
  comments: Comment[];
  isResolved: boolean;
  createdAt: string;
}

export interface Comment {
  id: string;
  content: string;
  author: DoctorDetail;
  createdAt: string;
  updatedAt?: string;
  mentions: string[]; // User IDs
  reactions?: Array<{ emoji: string; userId: string }>;
  isEdited: boolean;
  parentId?: string; // For nested replies
}

export interface Presence {
  id: string;
  caseId: string;
  user: DoctorDetail;
  section?: string;
  cursor?: { x: number; y: number };
  lastSeen: string;
  color: string;
}

export interface CollaborationState {
  activeUsers: Presence[];
  isEditing: boolean;
  hasConflicts: boolean;
  lastSyncedAt: string;
}

// =============================================================================
// Document Types
// =============================================================================

export interface CaseDocument {
  id: string;
  title: string;
  type:
    | "report"
    | "consent"
    | "referral"
    | "discharge"
    | "prescription"
    | "other";
  format: "pdf" | "docx" | "html";
  url: string;
  size: number;
  generatedAt: string;
  generatedBy: DoctorDetail;
  signedAt?: string;
  signedBy?: DoctorDetail;
  metadata?: Record<string, any>;
}

// =============================================================================
// Version History Types
// =============================================================================

export interface VersionHistoryEntry {
  id: string;
  version: number;
  timestamp: string;
  author: DoctorDetail;
  changeType: "create" | "update" | "delete";
  section: string;
  changes: Array<{
    field: string;
    oldValue: any;
    newValue: any;
  }>;
  snapshot?: Partial<CaseDetail>;
}

// =============================================================================
// API Request/Response Types
// =============================================================================

export interface UpdateCaseRequest {
  section: string;
  data: any;
  version: number; // Optimistic locking
}

export interface AddCommentRequest {
  sectionId: string;
  sectionType: string;
  content: string;
  mentions?: string[];
  parentId?: string;
}

export interface ExportOptions {
  format: "pdf" | "docx" | "html";
  sections: string[];
  includeImages: boolean;
  includeAIAnalysis: boolean;
  includeComments: boolean;
  isPrintOptimized: boolean;
}
