/**
 * NEURAXIS - Patient Validation Tests
 * Unit tests for Zod validation schemas
 */

import {
  demographicsSchema,
  emergencyContactSchema,
  getStepErrors,
  medicalHistorySchema,
  patientSchema,
  validateStep,
} from "@/lib/validations/patient";
import { describe, expect, it } from "@jest/globals";

describe("Demographics Schema Validation", () => {
  const validDemographics = {
    firstName: "John",
    lastName: "Doe",
    dateOfBirth: "1985-03-15",
    gender: "male",
    phonePrimary: "5551234567",
    addressLine1: "123 Main St",
    city: "New York",
    state: "New York",
    postalCode: "10001",
    country: "United States",
  };

  describe("firstName validation", () => {
    it("should accept valid first name", () => {
      const result = demographicsSchema.safeParse(validDemographics);
      expect(result.success).toBe(true);
    });

    it("should reject empty first name", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        firstName: "",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toContain("firstName");
      }
    });

    it("should reject first name with numbers", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        firstName: "John123",
      });
      expect(result.success).toBe(false);
    });

    it("should accept names with hyphens and apostrophes", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        firstName: "Mary-Jane O'Brien",
      });
      expect(result.success).toBe(true);
    });
  });

  describe("dateOfBirth validation", () => {
    it("should accept valid past date", () => {
      const result = demographicsSchema.safeParse(validDemographics);
      expect(result.success).toBe(true);
    });

    it("should reject future date", () => {
      const futureDate = new Date();
      futureDate.setFullYear(futureDate.getFullYear() + 1);

      const result = demographicsSchema.safeParse({
        ...validDemographics,
        dateOfBirth: futureDate.toISOString().split("T")[0],
      });
      expect(result.success).toBe(false);
    });

    it("should reject date before 1900", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        dateOfBirth: "1899-12-31",
      });
      expect(result.success).toBe(false);
    });
  });

  describe("phone validation", () => {
    it("should accept 10-digit phone number", () => {
      const result = demographicsSchema.safeParse(validDemographics);
      expect(result.success).toBe(true);
    });

    it("should accept formatted phone number", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        phonePrimary: "(555) 123-4567",
      });
      expect(result.success).toBe(true);
    });

    it("should accept international format", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        phonePrimary: "+1 555-123-4567",
      });
      expect(result.success).toBe(true);
    });

    it("should reject too short phone number", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        phonePrimary: "12345",
      });
      expect(result.success).toBe(false);
    });
  });

  describe("email validation", () => {
    it("should accept valid email", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        email: "john.doe@hospital.com",
      });
      expect(result.success).toBe(true);
    });

    it("should accept empty email (optional)", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        email: "",
      });
      expect(result.success).toBe(true);
    });

    it("should reject invalid email format", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        email: "not-an-email",
      });
      expect(result.success).toBe(false);
    });
  });

  describe("postalCode validation", () => {
    it("should accept valid US postal code", () => {
      const result = demographicsSchema.safeParse(validDemographics);
      expect(result.success).toBe(true);
    });

    it("should accept ZIP+4 format", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        postalCode: "10001-1234",
      });
      expect(result.success).toBe(true);
    });

    it("should reject too short postal code", () => {
      const result = demographicsSchema.safeParse({
        ...validDemographics,
        postalCode: "1234",
      });
      expect(result.success).toBe(false);
    });
  });
});

describe("Medical History Schema Validation", () => {
  describe("measurements validation", () => {
    it("should accept valid height and weight", () => {
      const result = medicalHistorySchema.safeParse({
        heightCm: 175,
        weightKg: 70,
      });
      expect(result.success).toBe(true);
    });

    it("should reject height below minimum", () => {
      const result = medicalHistorySchema.safeParse({
        heightCm: 10,
      });
      expect(result.success).toBe(false);
    });

    it("should reject height above maximum", () => {
      const result = medicalHistorySchema.safeParse({
        heightCm: 350,
      });
      expect(result.success).toBe(false);
    });

    it("should accept null values for optional fields", () => {
      const result = medicalHistorySchema.safeParse({
        heightCm: null,
        weightKg: null,
      });
      expect(result.success).toBe(true);
    });
  });

  describe("arrays validation", () => {
    it("should accept empty arrays", () => {
      const result = medicalHistorySchema.safeParse({
        allergies: [],
        chronicConditions: [],
        currentMedications: [],
        pastSurgeries: [],
      });
      expect(result.success).toBe(true);
    });

    it("should accept valid allergy list", () => {
      const result = medicalHistorySchema.safeParse({
        allergies: ["Penicillin", "Aspirin", "Latex"],
      });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.allergies).toHaveLength(3);
      }
    });
  });

  describe("bloodType validation", () => {
    it("should accept valid blood types", () => {
      const validTypes = [
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
        "unknown",
      ];

      validTypes.forEach((bloodType) => {
        const result = medicalHistorySchema.safeParse({ bloodType });
        expect(result.success).toBe(true);
      });
    });

    it("should reject invalid blood type", () => {
      const result = medicalHistorySchema.safeParse({
        bloodType: "C+",
      });
      expect(result.success).toBe(false);
    });
  });
});

describe("Emergency Contact Schema Validation", () => {
  const validEmergencyContact = {
    emergencyContactName: "Jane Doe",
    emergencyContactRelationship: "Spouse",
    emergencyContactPhone: "5559876543",
  };

  it("should accept valid emergency contact", () => {
    const result = emergencyContactSchema.safeParse(validEmergencyContact);
    expect(result.success).toBe(true);
  });

  it("should require emergency contact name", () => {
    const result = emergencyContactSchema.safeParse({
      ...validEmergencyContact,
      emergencyContactName: "",
    });
    expect(result.success).toBe(false);
  });

  it("should require emergency contact relationship", () => {
    const result = emergencyContactSchema.safeParse({
      ...validEmergencyContact,
      emergencyContactRelationship: "",
    });
    expect(result.success).toBe(false);
  });

  it("should validate emergency contact phone", () => {
    const result = emergencyContactSchema.safeParse({
      ...validEmergencyContact,
      emergencyContactPhone: "123",
    });
    expect(result.success).toBe(false);
  });

  it("should accept optional insurance fields", () => {
    const result = emergencyContactSchema.safeParse({
      ...validEmergencyContact,
      insuranceProvider: "Blue Cross",
      insurancePolicyNumber: "BC123456",
      insuranceGroupNumber: "GRP001",
    });
    expect(result.success).toBe(true);
  });
});

describe("Complete Patient Schema Validation", () => {
  const completePatientData = {
    // Demographics
    firstName: "Sarah",
    lastName: "Johnson",
    dateOfBirth: "1985-03-15",
    gender: "female",
    phonePrimary: "5551234567",
    addressLine1: "123 Main St",
    city: "New York",
    state: "New York",
    postalCode: "10001",
    country: "United States",
    // Medical History
    bloodType: "A+",
    allergies: ["Penicillin"],
    chronicConditions: ["Type 2 Diabetes"],
    currentMedications: ["Metformin"],
    pastSurgeries: [],
    // Emergency Contact
    emergencyContactName: "John Johnson",
    emergencyContactRelationship: "Spouse",
    emergencyContactPhone: "5559876543",
  };

  it("should accept complete valid patient data", () => {
    const result = patientSchema.safeParse(completePatientData);
    expect(result.success).toBe(true);
  });

  it("should reject incomplete patient data", () => {
    const { firstName, ...incomplete } = completePatientData;
    const result = patientSchema.safeParse(incomplete);
    expect(result.success).toBe(false);
  });
});

describe("Step Validation Helpers", () => {
  describe("validateStep", () => {
    it("should validate step 1 with demographics schema", () => {
      const result = validateStep(1, {
        firstName: "John",
        lastName: "Doe",
        dateOfBirth: "1985-03-15",
        gender: "male",
        phonePrimary: "5551234567",
        addressLine1: "123 Main St",
        city: "New York",
        state: "New York",
        postalCode: "10001",
        country: "United States",
      });
      expect(result.success).toBe(true);
    });

    it("should validate step 2 with medical history schema", () => {
      const result = validateStep(2, {
        allergies: ["Penicillin"],
        chronicConditions: [],
        currentMedications: [],
        pastSurgeries: [],
      });
      expect(result.success).toBe(true);
    });

    it("should validate step 3 with emergency contact schema", () => {
      const result = validateStep(3, {
        emergencyContactName: "Jane Doe",
        emergencyContactRelationship: "Spouse",
        emergencyContactPhone: "5559876543",
      });
      expect(result.success).toBe(true);
    });
  });

  describe("getStepErrors", () => {
    it("should return empty object for valid data", () => {
      const errors = getStepErrors(1, {
        firstName: "John",
        lastName: "Doe",
        dateOfBirth: "1985-03-15",
        gender: "male",
        phonePrimary: "5551234567",
        addressLine1: "123 Main St",
        city: "New York",
        state: "New York",
        postalCode: "10001",
        country: "United States",
      });
      expect(Object.keys(errors)).toHaveLength(0);
    });

    it("should return errors for invalid data", () => {
      const errors = getStepErrors(1, {
        firstName: "",
        lastName: "",
        dateOfBirth: "",
        gender: "male",
        phonePrimary: "123",
        addressLine1: "",
        city: "",
        state: "",
        postalCode: "1",
        country: "United States",
      });

      expect(errors.firstName).toBeDefined();
      expect(errors.lastName).toBeDefined();
      expect(errors.phonePrimary).toBeDefined();
    });
  });
});
