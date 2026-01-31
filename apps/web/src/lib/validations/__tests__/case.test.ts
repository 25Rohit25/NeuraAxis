/**
 * NEURAXIS - Case Validation Tests
 * Unit tests for case form validation schemas
 */

import { describe, expect, it } from "@jest/globals";
import {
  assessmentNotesSchema,
  chiefComplaintSchema,
  patientSelectionSchema,
  quickAddPatientSchema,
  symptomSchema,
  vitalSignsSchema,
} from "../case";

describe("Case Validation Schemas", () => {
  describe("patientSelectionSchema", () => {
    it("should validate correct patient selection", () => {
      const validPatient = {
        patientId: "550e8400-e29b-41d4-a716-446655440000",
        mrn: "MRN123456",
        fullName: "John Doe",
        dateOfBirth: "1985-03-15",
        age: 38,
        gender: "male",
      };

      const result = patientSelectionSchema.safeParse(validPatient);
      expect(result.success).toBe(true);
    });

    it("should reject invalid patient ID", () => {
      const invalidPatient = {
        patientId: "not-a-uuid",
        mrn: "MRN123456",
        fullName: "John Doe",
        dateOfBirth: "1985-03-15",
        age: 38,
        gender: "male",
      };

      const result = patientSelectionSchema.safeParse(invalidPatient);
      expect(result.success).toBe(false);
    });
  });

  describe("quickAddPatientSchema", () => {
    it("should validate correct quick add patient", () => {
      const validPatient = {
        firstName: "Jane",
        lastName: "Smith",
        dateOfBirth: "1990-07-20",
        gender: "female",
        phonePrimary: "1234567890",
        email: "jane@example.com",
      };

      const result = quickAddPatientSchema.safeParse(validPatient);
      expect(result.success).toBe(true);
    });

    it("should reject future date of birth", () => {
      const futureDate = new Date();
      futureDate.setFullYear(futureDate.getFullYear() + 1);

      const invalidPatient = {
        firstName: "Jane",
        lastName: "Smith",
        dateOfBirth: futureDate.toISOString().split("T")[0],
        gender: "female",
        phonePrimary: "1234567890",
      };

      const result = quickAddPatientSchema.safeParse(invalidPatient);
      expect(result.success).toBe(false);
    });

    it("should reject invalid gender", () => {
      const invalidPatient = {
        firstName: "Jane",
        lastName: "Smith",
        dateOfBirth: "1990-07-20",
        gender: "invalid",
        phonePrimary: "1234567890",
      };

      const result = quickAddPatientSchema.safeParse(invalidPatient);
      expect(result.success).toBe(false);
    });
  });

  describe("chiefComplaintSchema", () => {
    it("should validate correct chief complaint", () => {
      const validComplaint = {
        complaint: "Severe headache for the past 3 days",
        duration: "3",
        durationUnit: "days",
        onset: "gradual",
        severity: 7,
        location: "Frontal",
        aggravatingFactors: ["Light", "Noise"],
        relievingFactors: ["Rest", "Darkness"],
      };

      const result = chiefComplaintSchema.safeParse(validComplaint);
      expect(result.success).toBe(true);
    });

    it("should reject complaint that is too short", () => {
      const invalidComplaint = {
        complaint: "pain",
        duration: "3",
        durationUnit: "days",
        onset: "gradual",
        severity: 7,
      };

      const result = chiefComplaintSchema.safeParse(invalidComplaint);
      expect(result.success).toBe(false);
    });

    it("should reject invalid severity", () => {
      const invalidComplaint = {
        complaint: "Severe headache for the past 3 days",
        duration: "3",
        durationUnit: "days",
        onset: "gradual",
        severity: 15, // Out of range
      };

      const result = chiefComplaintSchema.safeParse(invalidComplaint);
      expect(result.success).toBe(false);
    });
  });

  describe("symptomSchema", () => {
    it("should validate correct symptom", () => {
      const validSymptom = {
        id: "symptom-1",
        code: "R51",
        name: "Headache",
        category: "neurological",
        severity: 6,
        duration: "3 days",
        notes: "Throbbing pain",
      };

      const result = symptomSchema.safeParse(validSymptom);
      expect(result.success).toBe(true);
    });

    it("should require severity between 1-10", () => {
      const invalidSymptom = {
        id: "symptom-1",
        code: "R51",
        name: "Headache",
        category: "neurological",
        severity: 0, // Too low
      };

      const result = symptomSchema.safeParse(invalidSymptom);
      expect(result.success).toBe(false);
    });
  });

  describe("vitalSignsSchema", () => {
    it("should validate correct vital signs", () => {
      const validVitals = {
        bloodPressureSystolic: 120,
        bloodPressureDiastolic: 80,
        heartRate: 72,
        temperature: 98.6,
        temperatureUnit: "F",
        oxygenSaturation: 98,
        respiratoryRate: 16,
        recordedAt: new Date().toISOString(),
      };

      const result = vitalSignsSchema.safeParse(validVitals);
      expect(result.success).toBe(true);
    });

    it("should reject systolic BP lower than diastolic", () => {
      const invalidVitals = {
        bloodPressureSystolic: 70,
        bloodPressureDiastolic: 80, // Higher than systolic
        heartRate: 72,
        temperature: 98.6,
        temperatureUnit: "F",
        oxygenSaturation: 98,
        respiratoryRate: 16,
        recordedAt: new Date().toISOString(),
      };

      const result = vitalSignsSchema.safeParse(invalidVitals);
      expect(result.success).toBe(false);
    });

    it("should reject O2 saturation over 100", () => {
      const invalidVitals = {
        bloodPressureSystolic: 120,
        bloodPressureDiastolic: 80,
        heartRate: 72,
        temperature: 98.6,
        temperatureUnit: "F",
        oxygenSaturation: 105, // Over 100%
        respiratoryRate: 16,
        recordedAt: new Date().toISOString(),
      };

      const result = vitalSignsSchema.safeParse(invalidVitals);
      expect(result.success).toBe(false);
    });
  });

  describe("assessmentNotesSchema", () => {
    it("should validate correct assessment", () => {
      const validAssessment = {
        clinicalImpression:
          "Patient presents with acute migraine with photophobia and phonophobia.",
        differentialDiagnosis: [
          "Migraine with aura",
          "Tension headache",
          "Cluster headache",
        ],
        recommendedTests: ["CT Head", "Complete blood count"],
        treatmentPlan: "Sumatriptan 50mg, NSAIDs",
        followUpInstructions: "Return if symptoms worsen",
        urgencyLevel: "moderate",
      };

      const result = assessmentNotesSchema.safeParse(validAssessment);
      expect(result.success).toBe(true);
    });

    it("should reject empty differential diagnosis", () => {
      const invalidAssessment = {
        clinicalImpression: "Patient presents with acute migraine.",
        differentialDiagnosis: [], // Empty
        recommendedTests: [],
        urgencyLevel: "moderate",
      };

      const result = assessmentNotesSchema.safeParse(invalidAssessment);
      expect(result.success).toBe(false);
    });

    it("should reject invalid urgency level", () => {
      const invalidAssessment = {
        clinicalImpression: "Patient presents with acute migraine.",
        differentialDiagnosis: ["Migraine"],
        recommendedTests: [],
        urgencyLevel: "urgent", // Invalid
      };

      const result = assessmentNotesSchema.safeParse(invalidAssessment);
      expect(result.success).toBe(false);
    });
  });
});
