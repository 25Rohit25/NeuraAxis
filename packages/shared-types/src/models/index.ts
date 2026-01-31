// ============================================
// Domain Model Types
// ============================================

import { PatientId, DiagnosisId, UserId, OrganizationId, Timestamp } from "../common";

/** Patient gender enum */
export enum Gender {
    MALE = "male",
    FEMALE = "female",
    OTHER = "other",
    PREFER_NOT_TO_SAY = "prefer_not_to_say",
}

/** Patient model */
export interface Patient {
    id: PatientId;
    organizationId: OrganizationId;
    firstName: string;
    lastName: string;
    dateOfBirth: string;
    gender: Gender;
    email?: string;
    phone?: string;
    address?: Address;
    medicalRecordNumber?: string;
    insuranceProvider?: string;
    insurancePolicyNumber?: string;
    emergencyContact?: EmergencyContact;
    allergies: string[];
    medications: string[];
    createdAt: Timestamp;
    updatedAt: Timestamp;
}

/** Address model */
export interface Address {
    street: string;
    city: string;
    state: string;
    postalCode: string;
    country: string;
}

/** Emergency contact model */
export interface EmergencyContact {
    name: string;
    relationship: string;
    phone: string;
}

/** Diagnosis status enum */
export enum DiagnosisStatus {
    PENDING = "pending",
    IN_PROGRESS = "in_progress",
    COMPLETED = "completed",
    REVIEWED = "reviewed",
    ARCHIVED = "archived",
}

/** Diagnosis severity enum */
export enum DiagnosisSeverity {
    LOW = "low",
    MODERATE = "moderate",
    HIGH = "high",
    CRITICAL = "critical",
}

/** Diagnosis model */
export interface Diagnosis {
    id: DiagnosisId;
    patientId: PatientId;
    createdBy: UserId;
    status: DiagnosisStatus;
    severity: DiagnosisSeverity;
    primaryDiagnosis: string;
    icdCode?: string;
    confidenceScore: number;
    differentialDiagnoses: DifferentialDiagnosis[];
    symptoms: string[];
    recommendations: string[];
    notes?: string;
    aiModelVersion: string;
    createdAt: Timestamp;
    updatedAt: Timestamp;
    reviewedAt?: Timestamp;
    reviewedBy?: UserId;
}

/** Differential diagnosis */
export interface DifferentialDiagnosis {
    name: string;
    icdCode?: string;
    probability: number;
    reasoning: string;
}

/** Medical image type enum */
export enum MedicalImageType {
    XRAY = "xray",
    CT_SCAN = "ct_scan",
    MRI = "mri",
    ULTRASOUND = "ultrasound",
    MAMMOGRAM = "mammogram",
    PET_SCAN = "pet_scan",
    OTHER = "other",
}

/** Medical image model */
export interface MedicalImage {
    id: string;
    patientId: PatientId;
    type: MedicalImageType;
    bodyRegion: string;
    fileUrl: string;
    thumbnailUrl?: string;
    metadata: Record<string, unknown>;
    uploadedAt: Timestamp;
    analyzedAt?: Timestamp;
}

/** User role enum */
export enum UserRole {
    ADMIN = "admin",
    PHYSICIAN = "physician",
    RADIOLOGIST = "radiologist",
    NURSE = "nurse",
    TECHNICIAN = "technician",
    PATIENT = "patient",
}

/** User model */
export interface User {
    id: UserId;
    organizationId: OrganizationId;
    email: string;
    firstName: string;
    lastName: string;
    role: UserRole;
    specialization?: string;
    licenseNumber?: string;
    isActive: boolean;
    lastLoginAt?: Timestamp;
    createdAt: Timestamp;
    updatedAt: Timestamp;
}

/** Organization model */
export interface Organization {
    id: OrganizationId;
    name: string;
    type: "hospital" | "clinic" | "laboratory" | "research";
    address: Address;
    phone: string;
    email: string;
    website?: string;
    isActive: boolean;
    createdAt: Timestamp;
    updatedAt: Timestamp;
}
