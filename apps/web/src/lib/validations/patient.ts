/**
 * NEURAXIS - Patient Validation Schemas (Frontend)
 * Zod schemas for multi-step patient registration form
 */

import { z } from "zod";

// =============================================================================
// Enums
// =============================================================================

export const Gender = z.enum(["male", "female", "other", "prefer_not_to_say"]);
export type Gender = z.infer<typeof Gender>;

export const MaritalStatus = z.enum([
  "single",
  "married",
  "divorced",
  "widowed",
  "separated",
  "domestic_partnership",
]);
export type MaritalStatus = z.infer<typeof MaritalStatus>;

export const BloodType = z.enum([
  "A+",
  "A-",
  "B+",
  "B-",
  "AB+",
  "AB-",
  "O+",
  "O-",
  "unknown",
]);
export type BloodType = z.infer<typeof BloodType>;

// =============================================================================
// Step 1: Demographics Schema
// =============================================================================

export const demographicsSchema = z.object({
  // Personal Information
  firstName: z
    .string()
    .min(1, "First name is required")
    .max(100, "First name must be less than 100 characters")
    .regex(
      /^[a-zA-Z\s'-]+$/,
      "First name can only contain letters, spaces, hyphens, and apostrophes"
    ),

  middleName: z
    .string()
    .max(100, "Middle name must be less than 100 characters")
    .regex(
      /^[a-zA-Z\s'-]*$/,
      "Middle name can only contain letters, spaces, hyphens, and apostrophes"
    )
    .optional()
    .or(z.literal("")),

  lastName: z
    .string()
    .min(1, "Last name is required")
    .max(100, "Last name must be less than 100 characters")
    .regex(
      /^[a-zA-Z\s'-]+$/,
      "Last name can only contain letters, spaces, hyphens, and apostrophes"
    ),

  dateOfBirth: z
    .string()
    .min(1, "Date of birth is required")
    .refine(
      (val) => {
        const date = new Date(val);
        const today = new Date();
        return date <= today;
      },
      { message: "Date of birth cannot be in the future" }
    )
    .refine(
      (val) => {
        const date = new Date(val);
        return date.getFullYear() >= 1900;
      },
      { message: "Date of birth must be after 1900" }
    ),

  gender: Gender,

  maritalStatus: MaritalStatus.optional(),

  // Contact Information
  email: z
    .string()
    .email("Please enter a valid email address")
    .optional()
    .or(z.literal("")),

  phonePrimary: z
    .string()
    .min(10, "Phone number must be at least 10 digits")
    .max(20, "Phone number must be less than 20 characters")
    .regex(/^[\d\s\-\(\)\+]+$/, "Please enter a valid phone number"),

  phoneSecondary: z
    .string()
    .max(20, "Phone number must be less than 20 characters")
    .regex(/^[\d\s\-\(\)\+]*$/, "Please enter a valid phone number")
    .optional()
    .or(z.literal("")),

  // Address
  addressLine1: z
    .string()
    .min(1, "Address is required")
    .max(255, "Address must be less than 255 characters"),

  addressLine2: z
    .string()
    .max(255, "Address must be less than 255 characters")
    .optional()
    .or(z.literal("")),

  city: z
    .string()
    .min(1, "City is required")
    .max(100, "City must be less than 100 characters"),

  state: z
    .string()
    .min(1, "State is required")
    .max(100, "State must be less than 100 characters"),

  postalCode: z
    .string()
    .min(5, "Postal code must be at least 5 characters")
    .max(20, "Postal code must be less than 20 characters")
    .regex(/^[\dA-Za-z\s\-]+$/, "Please enter a valid postal code"),

  country: z
    .string()
    .min(1, "Country is required")
    .max(100, "Country must be less than 100 characters")
    .default("United States"),
});

export type DemographicsFormData = z.infer<typeof demographicsSchema>;

// =============================================================================
// Step 2: Medical History Schema
// =============================================================================

export const medicalHistorySchema = z.object({
  bloodType: BloodType.optional(),

  heightCm: z
    .number()
    .min(30, "Height must be at least 30 cm")
    .max(300, "Height must be less than 300 cm")
    .optional()
    .nullable(),

  weightKg: z
    .number()
    .min(0.5, "Weight must be at least 0.5 kg")
    .max(700, "Weight must be less than 700 kg")
    .optional()
    .nullable(),

  allergies: z.array(z.string()).default([]),

  chronicConditions: z.array(z.string()).default([]),

  currentMedications: z.array(z.string()).default([]),

  pastSurgeries: z.array(z.string()).default([]),

  familyHistory: z
    .string()
    .max(5000, "Family history must be less than 5000 characters")
    .optional()
    .or(z.literal("")),
});

export type MedicalHistoryFormData = z.infer<typeof medicalHistorySchema>;

// =============================================================================
// Step 3: Emergency Contact Schema
// =============================================================================

export const emergencyContactSchema = z.object({
  // Emergency Contact
  emergencyContactName: z
    .string()
    .min(1, "Emergency contact name is required")
    .max(200, "Name must be less than 200 characters"),

  emergencyContactRelationship: z
    .string()
    .min(1, "Relationship is required")
    .max(50, "Relationship must be less than 50 characters"),

  emergencyContactPhone: z
    .string()
    .min(10, "Phone number must be at least 10 digits")
    .max(20, "Phone number must be less than 20 characters")
    .regex(/^[\d\s\-\(\)\+]+$/, "Please enter a valid phone number"),

  emergencyContactEmail: z
    .string()
    .email("Please enter a valid email address")
    .optional()
    .or(z.literal("")),

  // Insurance Information
  insuranceProvider: z
    .string()
    .max(200, "Insurance provider must be less than 200 characters")
    .optional()
    .or(z.literal("")),

  insurancePolicyNumber: z
    .string()
    .max(100, "Policy number must be less than 100 characters")
    .optional()
    .or(z.literal("")),

  insuranceGroupNumber: z
    .string()
    .max(100, "Group number must be less than 100 characters")
    .optional()
    .or(z.literal("")),
});

export type EmergencyContactFormData = z.infer<typeof emergencyContactSchema>;

// =============================================================================
// Complete Patient Schema
// =============================================================================

export const patientSchema = demographicsSchema
  .merge(medicalHistorySchema)
  .merge(emergencyContactSchema);

export type PatientFormData = z.infer<typeof patientSchema>;

// =============================================================================
// Default Values
// =============================================================================

export const defaultDemographics: DemographicsFormData = {
  firstName: "",
  middleName: "",
  lastName: "",
  dateOfBirth: "",
  gender: "prefer_not_to_say",
  maritalStatus: undefined,
  email: "",
  phonePrimary: "",
  phoneSecondary: "",
  addressLine1: "",
  addressLine2: "",
  city: "",
  state: "",
  postalCode: "",
  country: "United States",
};

export const defaultMedicalHistory: MedicalHistoryFormData = {
  bloodType: undefined,
  heightCm: null,
  weightKg: null,
  allergies: [],
  chronicConditions: [],
  currentMedications: [],
  pastSurgeries: [],
  familyHistory: "",
};

export const defaultEmergencyContact: EmergencyContactFormData = {
  emergencyContactName: "",
  emergencyContactRelationship: "",
  emergencyContactPhone: "",
  emergencyContactEmail: "",
  insuranceProvider: "",
  insurancePolicyNumber: "",
  insuranceGroupNumber: "",
};

export const defaultPatientFormData: PatientFormData = {
  ...defaultDemographics,
  ...defaultMedicalHistory,
  ...defaultEmergencyContact,
};

// =============================================================================
// Validation Helpers
// =============================================================================

export function validateStep(step: number, data: Partial<PatientFormData>) {
  switch (step) {
    case 1:
      return demographicsSchema.safeParse(data);
    case 2:
      return medicalHistorySchema.safeParse(data);
    case 3:
      return emergencyContactSchema.safeParse(data);
    default:
      return patientSchema.safeParse(data);
  }
}

export function getStepErrors(step: number, data: Partial<PatientFormData>) {
  const result = validateStep(step, data);
  if (result.success) return {};

  return result.error.issues.reduce(
    (acc, issue) => {
      const path = issue.path.join(".");
      acc[path] = issue.message;
      return acc;
    },
    {} as Record<string, string>
  );
}
