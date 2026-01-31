"use server";

/**
 * NEURAXIS - Patient Server Actions
 * Next.js Server Actions for patient registration
 */

import { patientSchema, type PatientFormData } from "@/lib/validations/patient";
import { revalidatePath } from "next/cache";

// API base URL from environment
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// =============================================================================
// Types
// =============================================================================

export interface ActionResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  errors?: Record<string, string>;
}

export interface PatientCreateResult {
  id: string;
  mrn: string;
}

export interface DuplicateCheckResult {
  hasDuplicates: boolean;
  potentialDuplicates: Array<{
    id: string;
    mrn: string;
    fullName: string;
    dateOfBirth: string;
    similarityScore: number;
    matchReason: string;
  }>;
}

// =============================================================================
// Helper Functions
// =============================================================================

async function getAuthHeaders(): Promise<Record<string, string>> {
  // TODO: Get auth token from session
  // const session = await getServerSession(authOptions);
  // const token = session?.accessToken;

  return {
    "Content-Type": "application/json",
    // 'Authorization': `Bearer ${token}`,
  };
}

function transformFormDataToApi(
  data: PatientFormData
): Record<string, unknown> {
  // Transform camelCase keys to snake_case for API
  return {
    first_name: data.firstName,
    middle_name: data.middleName || null,
    last_name: data.lastName,
    date_of_birth: data.dateOfBirth,
    gender: data.gender,
    marital_status: data.maritalStatus || null,
    email: data.email || null,
    phone_primary: data.phonePrimary,
    phone_secondary: data.phoneSecondary || null,
    address_line1: data.addressLine1,
    address_line2: data.addressLine2 || null,
    city: data.city,
    state: data.state,
    postal_code: data.postalCode,
    country: data.country,
    blood_type: data.bloodType || null,
    height_cm: data.heightCm || null,
    weight_kg: data.weightKg || null,
    allergies: data.allergies,
    chronic_conditions: data.chronicConditions,
    current_medications: data.currentMedications,
    past_surgeries: data.pastSurgeries,
    family_history: data.familyHistory || null,
    emergency_contact_name: data.emergencyContactName,
    emergency_contact_relationship: data.emergencyContactRelationship,
    emergency_contact_phone: data.emergencyContactPhone,
    emergency_contact_email: data.emergencyContactEmail || null,
    insurance_provider: data.insuranceProvider || null,
    insurance_policy_number: data.insurancePolicyNumber || null,
    insurance_group_number: data.insuranceGroupNumber || null,
  };
}

// =============================================================================
// Server Actions
// =============================================================================

/**
 * Register a new patient
 */
export async function registerPatient(
  formData: PatientFormData
): Promise<ActionResult<PatientCreateResult>> {
  try {
    // Validate form data
    const validationResult = patientSchema.safeParse(formData);

    if (!validationResult.success) {
      const errors = validationResult.error.issues.reduce(
        (acc, issue) => {
          const path = issue.path.join(".");
          acc[path] = issue.message;
          return acc;
        },
        {} as Record<string, string>
      );

      return {
        success: false,
        error: "Validation failed",
        errors,
      };
    }

    // Transform data for API
    const apiData = transformFormDataToApi(validationResult.data);

    // Make API request
    const response = await fetch(`${API_BASE_URL}/patients`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(apiData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Handle duplicate detection
      if (response.status === 409) {
        return {
          success: false,
          error:
            errorData.detail?.message ||
            "A patient with similar information already exists",
          errors: {
            duplicate: errorData.detail?.existing_mrn || "Unknown",
          },
        };
      }

      return {
        success: false,
        error: errorData.detail || "Failed to register patient",
      };
    }

    const patient = await response.json();

    // Revalidate patients list
    revalidatePath("/patients");

    return {
      success: true,
      data: {
        id: patient.id,
        mrn: patient.mrn,
      },
    };
  } catch (error) {
    console.error("Failed to register patient:", error);
    return {
      success: false,
      error: "An unexpected error occurred. Please try again.",
    };
  }
}

/**
 * Check for duplicate patients
 */
export async function checkDuplicates(
  firstName: string,
  lastName: string,
  dateOfBirth: string
): Promise<ActionResult<DuplicateCheckResult>> {
  try {
    const response = await fetch(`${API_BASE_URL}/patients/check-duplicates`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dateOfBirth,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errorData.detail || "Failed to check for duplicates",
      };
    }

    const result = await response.json();

    return {
      success: true,
      data: {
        hasDuplicates: result.has_duplicates,
        potentialDuplicates: result.potential_duplicates.map((d: any) => ({
          id: d.id,
          mrn: d.mrn,
          fullName: d.full_name,
          dateOfBirth: d.date_of_birth,
          similarityScore: d.similarity_score,
          matchReason: d.match_reason,
        })),
      },
    };
  } catch (error) {
    console.error("Failed to check duplicates:", error);
    return {
      success: false,
      error: "Failed to check for duplicates",
    };
  }
}

/**
 * Upload insurance document
 */
export async function uploadInsuranceDocument(
  patientId: string,
  file: File
): Promise<ActionResult<{ documentUrl: string }>> {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const headers = await getAuthHeaders();
    // Remove Content-Type for FormData - browser will set it with boundary
    delete (headers as any)["Content-Type"];

    const response = await fetch(
      `${API_BASE_URL}/patients/${patientId}/insurance-document`,
      {
        method: "POST",
        headers,
        body: formData,
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: errorData.detail || "Failed to upload document",
      };
    }

    const result = await response.json();

    return {
      success: true,
      data: {
        documentUrl: result.document_url,
      },
    };
  } catch (error) {
    console.error("Failed to upload document:", error);
    return {
      success: false,
      error: "Failed to upload document",
    };
  }
}

/**
 * Get city suggestions for autocomplete
 */
export async function getCitySuggestions(
  query: string,
  state?: string
): Promise<ActionResult<string[]>> {
  // In production, this would call a geocoding API
  // For now, return common US cities
  const cities = [
    "New York",
    "Los Angeles",
    "Chicago",
    "Houston",
    "Phoenix",
    "Philadelphia",
    "San Antonio",
    "San Diego",
    "Dallas",
    "San Jose",
    "Austin",
    "Jacksonville",
    "Fort Worth",
    "Columbus",
    "Charlotte",
    "San Francisco",
    "Indianapolis",
    "Seattle",
    "Denver",
    "Boston",
    "El Paso",
    "Nashville",
    "Detroit",
    "Portland",
    "Las Vegas",
    "Memphis",
    "Baltimore",
    "Milwaukee",
    "Albuquerque",
    "Tucson",
  ];

  const filtered = cities
    .filter((city) => city.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 10);

  return {
    success: true,
    data: filtered,
  };
}

/**
 * Get medication suggestions for autocomplete
 */
export async function getMedicationSuggestions(
  query: string
): Promise<ActionResult<string[]>> {
  // Common medications - in production, use RxNorm API
  const medications = [
    "Lisinopril",
    "Atorvastatin",
    "Levothyroxine",
    "Metformin",
    "Amlodipine",
    "Metoprolol",
    "Omeprazole",
    "Simvastatin",
    "Losartan",
    "Gabapentin",
    "Hydrochlorothiazide",
    "Sertraline",
    "Acetaminophen",
    "Ibuprofen",
    "Aspirin",
    "Prednisone",
    "Amoxicillin",
    "Azithromycin",
    "Fluoxetine",
    "Tramadol",
    "Pantoprazole",
    "Furosemide",
    "Clopidogrel",
    "Warfarin",
    "Insulin",
  ];

  const filtered = medications
    .filter((med) => med.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 10);

  return {
    success: true,
    data: filtered,
  };
}

/**
 * Get condition suggestions for autocomplete
 */
export async function getConditionSuggestions(
  query: string
): Promise<ActionResult<string[]>> {
  // Common conditions - in production, use ICD-10 API
  const conditions = [
    "Type 2 Diabetes Mellitus",
    "Essential Hypertension",
    "Hyperlipidemia",
    "Coronary Artery Disease",
    "Chronic Kidney Disease",
    "Chronic Obstructive Pulmonary Disease (COPD)",
    "Asthma",
    "Depression",
    "Anxiety Disorder",
    "Hypothyroidism",
    "Atrial Fibrillation",
    "Heart Failure",
    "Osteoarthritis",
    "Rheumatoid Arthritis",
    "Gastroesophageal Reflux Disease (GERD)",
    "Migraine",
    "Epilepsy",
    "Sleep Apnea",
    "Obesity",
    "Anemia",
  ];

  const filtered = conditions
    .filter((cond) => cond.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 10);

  return {
    success: true,
    data: filtered,
  };
}

/**
 * Get allergy suggestions for autocomplete
 */
export async function getAllergySuggestions(
  query: string
): Promise<ActionResult<string[]>> {
  const allergies = [
    "Penicillin",
    "Sulfa Drugs",
    "Aspirin",
    "NSAIDs",
    "Codeine",
    "Morphine",
    "Latex",
    "Contrast Dye",
    "Peanuts",
    "Tree Nuts",
    "Shellfish",
    "Eggs",
    "Milk",
    "Soy",
    "Wheat",
    "Fish",
    "Bee Stings",
    "Dust Mites",
    "Pollen",
    "Mold",
    "Pet Dander",
    "Nickel",
    "Amoxicillin",
    "Cephalosporins",
    "Sulfonamides",
  ];

  const filtered = allergies
    .filter((allergy) => allergy.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 10);

  return {
    success: true,
    data: filtered,
  };
}
