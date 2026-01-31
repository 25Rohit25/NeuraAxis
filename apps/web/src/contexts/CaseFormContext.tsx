/**
 * NEURAXIS - Case Form Context
 * React Context for managing multi-step case creation form state
 */

"use client";

import type {
  AssessmentNotes,
  CaseDraft,
  CaseFormData,
  CaseImage,
  ChiefComplaint,
  CurrentMedication,
  MedicalHistory,
  PatientSelection,
  Symptom,
  VitalSigns,
} from "@/types/medical-case";
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useReducer,
  useRef,
} from "react";
import { v4 as uuidv4 } from "uuid";

// =============================================================================
// Initial State
// =============================================================================

const initialFormData: CaseFormData = {
  currentStep: 0,
  completedSteps: [],
  patient: null,
  chiefComplaint: null,
  symptoms: [],
  vitals: null,
  medicalHistory: null,
  medications: [],
  images: [],
  assessment: null,
  draftId: undefined,
  lastSavedAt: undefined,
  isDirty: false,
};

// =============================================================================
// Action Types
// =============================================================================

type CaseFormAction =
  | { type: "SET_STEP"; payload: number }
  | { type: "COMPLETE_STEP"; payload: number }
  | { type: "SET_PATIENT"; payload: PatientSelection | null }
  | { type: "SET_CHIEF_COMPLAINT"; payload: ChiefComplaint | null }
  | { type: "ADD_SYMPTOM"; payload: Symptom }
  | { type: "UPDATE_SYMPTOM"; payload: { id: string; data: Partial<Symptom> } }
  | { type: "REMOVE_SYMPTOM"; payload: string }
  | { type: "SET_SYMPTOMS"; payload: Symptom[] }
  | { type: "SET_VITALS"; payload: VitalSigns | null }
  | { type: "SET_MEDICAL_HISTORY"; payload: MedicalHistory | null }
  | { type: "ADD_MEDICATION"; payload: CurrentMedication }
  | {
      type: "UPDATE_MEDICATION";
      payload: { id: string; data: Partial<CurrentMedication> };
    }
  | { type: "REMOVE_MEDICATION"; payload: string }
  | { type: "SET_MEDICATIONS"; payload: CurrentMedication[] }
  | { type: "ADD_IMAGE"; payload: CaseImage }
  | { type: "UPDATE_IMAGE"; payload: { id: string; data: Partial<CaseImage> } }
  | { type: "REMOVE_IMAGE"; payload: string }
  | { type: "SET_ASSESSMENT"; payload: AssessmentNotes | null }
  | { type: "LOAD_DRAFT"; payload: CaseDraft }
  | {
      type: "SAVE_DRAFT_SUCCESS";
      payload: { draftId: string; savedAt: string };
    }
  | { type: "MARK_DIRTY" }
  | { type: "MARK_CLEAN" }
  | { type: "RESET_FORM" };

// =============================================================================
// Reducer
// =============================================================================

function caseFormReducer(
  state: CaseFormData,
  action: CaseFormAction
): CaseFormData {
  switch (action.type) {
    case "SET_STEP":
      return { ...state, currentStep: action.payload };

    case "COMPLETE_STEP":
      return {
        ...state,
        completedSteps: state.completedSteps.includes(action.payload)
          ? state.completedSteps
          : [...state.completedSteps, action.payload],
      };

    case "SET_PATIENT":
      return { ...state, patient: action.payload, isDirty: true };

    case "SET_CHIEF_COMPLAINT":
      return { ...state, chiefComplaint: action.payload, isDirty: true };

    case "ADD_SYMPTOM":
      return {
        ...state,
        symptoms: [...state.symptoms, action.payload],
        isDirty: true,
      };

    case "UPDATE_SYMPTOM":
      return {
        ...state,
        symptoms: state.symptoms.map((s) =>
          s.id === action.payload.id ? { ...s, ...action.payload.data } : s
        ),
        isDirty: true,
      };

    case "REMOVE_SYMPTOM":
      return {
        ...state,
        symptoms: state.symptoms.filter((s) => s.id !== action.payload),
        isDirty: true,
      };

    case "SET_SYMPTOMS":
      return { ...state, symptoms: action.payload, isDirty: true };

    case "SET_VITALS":
      return { ...state, vitals: action.payload, isDirty: true };

    case "SET_MEDICAL_HISTORY":
      return { ...state, medicalHistory: action.payload, isDirty: true };

    case "ADD_MEDICATION":
      return {
        ...state,
        medications: [...state.medications, action.payload],
        isDirty: true,
      };

    case "UPDATE_MEDICATION":
      return {
        ...state,
        medications: state.medications.map((m) =>
          m.id === action.payload.id ? { ...m, ...action.payload.data } : m
        ),
        isDirty: true,
      };

    case "REMOVE_MEDICATION":
      return {
        ...state,
        medications: state.medications.filter((m) => m.id !== action.payload),
        isDirty: true,
      };

    case "SET_MEDICATIONS":
      return { ...state, medications: action.payload, isDirty: true };

    case "ADD_IMAGE":
      return {
        ...state,
        images: [...state.images, action.payload],
        isDirty: true,
      };

    case "UPDATE_IMAGE":
      return {
        ...state,
        images: state.images.map((i) =>
          i.id === action.payload.id ? { ...i, ...action.payload.data } : i
        ),
        isDirty: true,
      };

    case "REMOVE_IMAGE":
      return {
        ...state,
        images: state.images.filter((i) => i.id !== action.payload),
        isDirty: true,
      };

    case "SET_ASSESSMENT":
      return { ...state, assessment: action.payload, isDirty: true };

    case "LOAD_DRAFT":
      return {
        ...initialFormData,
        ...action.payload.data,
        draftId: action.payload.id,
        lastSavedAt: action.payload.updatedAt,
        isDirty: false,
      };

    case "SAVE_DRAFT_SUCCESS":
      return {
        ...state,
        draftId: action.payload.draftId,
        lastSavedAt: action.payload.savedAt,
        isDirty: false,
      };

    case "MARK_DIRTY":
      return { ...state, isDirty: true };

    case "MARK_CLEAN":
      return { ...state, isDirty: false };

    case "RESET_FORM":
      return initialFormData;

    default:
      return state;
  }
}

// =============================================================================
// Context
// =============================================================================

interface CaseFormContextValue {
  state: CaseFormData;
  dispatch: React.Dispatch<CaseFormAction>;

  // Navigation
  goToStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;

  // Step data setters
  setPatient: (patient: PatientSelection | null) => void;
  setChiefComplaint: (complaint: ChiefComplaint | null) => void;
  addSymptom: (symptom: Omit<Symptom, "id">) => void;
  updateSymptom: (id: string, data: Partial<Symptom>) => void;
  removeSymptom: (id: string) => void;
  setVitals: (vitals: VitalSigns | null) => void;
  setMedicalHistory: (history: MedicalHistory | null) => void;
  addMedication: (medication: Omit<CurrentMedication, "id">) => void;
  updateMedication: (id: string, data: Partial<CurrentMedication>) => void;
  removeMedication: (id: string) => void;
  setMedications: (medications: CurrentMedication[]) => void;
  addImage: (image: Omit<CaseImage, "id">) => void;
  updateImage: (id: string, data: Partial<CaseImage>) => void;
  removeImage: (id: string) => void;
  setAssessment: (assessment: AssessmentNotes | null) => void;

  // Draft management
  saveDraft: () => Promise<void>;
  loadDraft: (draftId: string) => Promise<void>;
  resetForm: () => void;

  // Validation
  isStepComplete: (step: number) => boolean;
  canSubmit: () => boolean;

  // Status
  isSaving: boolean;
  saveError: string | null;
}

const CaseFormContext = createContext<CaseFormContextValue | null>(null);

// =============================================================================
// Provider
// =============================================================================

interface CaseFormProviderProps {
  children: React.ReactNode;
  initialDraftId?: string;
  autoSaveIntervalMs?: number;
}

export function CaseFormProvider({
  children,
  initialDraftId,
  autoSaveIntervalMs = 30000, // 30 seconds
}: CaseFormProviderProps) {
  const [state, dispatch] = useReducer(caseFormReducer, initialFormData);
  const [isSaving, setIsSaving] = React.useState(false);
  const [saveError, setSaveError] = React.useState<string | null>(null);
  const autoSaveRef = useRef<NodeJS.Timeout | null>(null);

  // Load initial draft
  useEffect(() => {
    if (initialDraftId) {
      loadDraft(initialDraftId);
    }
  }, [initialDraftId]);

  // Auto-save
  useEffect(() => {
    if (state.isDirty && autoSaveIntervalMs > 0) {
      autoSaveRef.current = setTimeout(() => {
        saveDraft();
      }, autoSaveIntervalMs);
    }

    return () => {
      if (autoSaveRef.current) {
        clearTimeout(autoSaveRef.current);
      }
    };
  }, [state.isDirty, state, autoSaveIntervalMs]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (state.isDirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [state.isDirty]);

  // Navigation
  const goToStep = useCallback((step: number) => {
    dispatch({ type: "SET_STEP", payload: step });
  }, []);

  const nextStep = useCallback(() => {
    dispatch({ type: "COMPLETE_STEP", payload: state.currentStep });
    dispatch({ type: "SET_STEP", payload: state.currentStep + 1 });
  }, [state.currentStep]);

  const prevStep = useCallback(() => {
    dispatch({ type: "SET_STEP", payload: Math.max(0, state.currentStep - 1) });
  }, [state.currentStep]);

  // Step data setters
  const setPatient = useCallback((patient: PatientSelection | null) => {
    dispatch({ type: "SET_PATIENT", payload: patient });
  }, []);

  const setChiefComplaint = useCallback((complaint: ChiefComplaint | null) => {
    dispatch({ type: "SET_CHIEF_COMPLAINT", payload: complaint });
  }, []);

  const addSymptom = useCallback((symptom: Omit<Symptom, "id">) => {
    dispatch({ type: "ADD_SYMPTOM", payload: { ...symptom, id: uuidv4() } });
  }, []);

  const updateSymptom = useCallback((id: string, data: Partial<Symptom>) => {
    dispatch({ type: "UPDATE_SYMPTOM", payload: { id, data } });
  }, []);

  const removeSymptom = useCallback((id: string) => {
    dispatch({ type: "REMOVE_SYMPTOM", payload: id });
  }, []);

  const setVitals = useCallback((vitals: VitalSigns | null) => {
    dispatch({ type: "SET_VITALS", payload: vitals });
  }, []);

  const setMedicalHistory = useCallback((history: MedicalHistory | null) => {
    dispatch({ type: "SET_MEDICAL_HISTORY", payload: history });
  }, []);

  const addMedication = useCallback(
    (medication: Omit<CurrentMedication, "id">) => {
      dispatch({
        type: "ADD_MEDICATION",
        payload: { ...medication, id: uuidv4() },
      });
    },
    []
  );

  const updateMedication = useCallback(
    (id: string, data: Partial<CurrentMedication>) => {
      dispatch({ type: "UPDATE_MEDICATION", payload: { id, data } });
    },
    []
  );

  const removeMedication = useCallback((id: string) => {
    dispatch({ type: "REMOVE_MEDICATION", payload: id });
  }, []);

  const setMedications = useCallback((medications: CurrentMedication[]) => {
    dispatch({ type: "SET_MEDICATIONS", payload: medications });
  }, []);

  const addImage = useCallback((image: Omit<CaseImage, "id">) => {
    dispatch({ type: "ADD_IMAGE", payload: { ...image, id: uuidv4() } });
  }, []);

  const updateImage = useCallback((id: string, data: Partial<CaseImage>) => {
    dispatch({ type: "UPDATE_IMAGE", payload: { id, data } });
  }, []);

  const removeImage = useCallback((id: string) => {
    dispatch({ type: "REMOVE_IMAGE", payload: id });
  }, []);

  const setAssessment = useCallback((assessment: AssessmentNotes | null) => {
    dispatch({ type: "SET_ASSESSMENT", payload: assessment });
  }, []);

  // Draft management
  const saveDraft = useCallback(async () => {
    if (!state.isDirty && state.draftId) return;

    setIsSaving(true);
    setSaveError(null);

    try {
      const response = await fetch("/api/cases/drafts", {
        method: state.draftId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: state.draftId,
          patientId: state.patient?.patientId,
          patientName: state.patient?.fullName,
          chiefComplaint: state.chiefComplaint?.complaint,
          currentStep: state.currentStep,
          data: state,
        }),
      });

      if (!response.ok) throw new Error("Failed to save draft");

      const result = await response.json();
      dispatch({
        type: "SAVE_DRAFT_SUCCESS",
        payload: { draftId: result.id, savedAt: new Date().toISOString() },
      });
    } catch (error) {
      setSaveError("Failed to save draft");
      console.error("Draft save error:", error);
    } finally {
      setIsSaving(false);
    }
  }, [state]);

  const loadDraft = useCallback(async (draftId: string) => {
    try {
      const response = await fetch(`/api/cases/drafts/${draftId}`);
      if (!response.ok) throw new Error("Draft not found");

      const draft: CaseDraft = await response.json();
      dispatch({ type: "LOAD_DRAFT", payload: draft });
    } catch (error) {
      console.error("Draft load error:", error);
    }
  }, []);

  const resetForm = useCallback(() => {
    dispatch({ type: "RESET_FORM" });
  }, []);

  // Validation
  const isStepComplete = useCallback(
    (step: number): boolean => {
      switch (step) {
        case 0:
          return state.patient !== null;
        case 1:
          return (
            state.chiefComplaint !== null &&
            state.chiefComplaint.complaint.length > 0
          );
        case 2:
          return state.symptoms.length > 0;
        case 3:
          return state.vitals !== null;
        case 4:
          return true; // Optional
        case 5:
          return true; // Optional
        case 6:
          return true; // Optional
        case 7:
          return (
            state.assessment !== null &&
            state.assessment.clinicalImpression.length > 0
          );
        default:
          return false;
      }
    },
    [state]
  );

  const canSubmit = useCallback((): boolean => {
    return (
      isStepComplete(0) &&
      isStepComplete(1) &&
      isStepComplete(2) &&
      isStepComplete(3) &&
      isStepComplete(7)
    );
  }, [isStepComplete]);

  const value: CaseFormContextValue = {
    state,
    dispatch,
    goToStep,
    nextStep,
    prevStep,
    setPatient,
    setChiefComplaint,
    addSymptom,
    updateSymptom,
    removeSymptom,
    setVitals,
    setMedicalHistory,
    addMedication,
    updateMedication,
    removeMedication,
    setMedications,
    addImage,
    updateImage,
    removeImage,
    setAssessment,
    saveDraft,
    loadDraft,
    resetForm,
    isStepComplete,
    canSubmit,
    isSaving,
    saveError,
  };

  return (
    <CaseFormContext.Provider value={value}>
      {children}
    </CaseFormContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

export function useCaseForm() {
  const context = useContext(CaseFormContext);
  if (!context) {
    throw new Error("useCaseForm must be used within a CaseFormProvider");
  }
  return context;
}

export { CaseFormContext };
