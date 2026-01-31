/**
 * NEURAXIS - Case Dashboard Types
 * TypeScript types for the medical case dashboard
 */

// =============================================================================
// Enums & Constants
// =============================================================================

export type CasePriority = "low" | "moderate" | "high" | "critical";
export type CaseStatus =
  | "draft"
  | "pending"
  | "in_progress"
  | "review"
  | "completed"
  | "archived";
export type DashboardView = "active" | "urgent" | "pending" | "closed" | "team";

export const PRIORITY_CONFIG: Record<
  CasePriority,
  { label: string; color: string; bgColor: string }
> = {
  low: { label: "Low", color: "text-success", bgColor: "bg-success/10" },
  moderate: {
    label: "Moderate",
    color: "text-warning",
    bgColor: "bg-warning/10",
  },
  high: {
    label: "High",
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
  },
  critical: {
    label: "Critical",
    color: "text-danger",
    bgColor: "bg-danger/10",
  },
};

export const STATUS_CONFIG: Record<
  CaseStatus,
  { label: string; color: string; bgColor: string }
> = {
  draft: {
    label: "Draft",
    color: "text-muted-foreground",
    bgColor: "bg-muted",
  },
  pending: {
    label: "Pending",
    color: "text-warning",
    bgColor: "bg-warning/10",
  },
  in_progress: {
    label: "In Progress",
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
  review: { label: "Review", color: "text-info", bgColor: "bg-info/10" },
  completed: {
    label: "Completed",
    color: "text-success",
    bgColor: "bg-success/10",
  },
  archived: {
    label: "Archived",
    color: "text-muted-foreground",
    bgColor: "bg-muted",
  },
};

// =============================================================================
// Case Types
// =============================================================================

export interface CasePatient {
  id: string;
  mrn: string;
  fullName: string;
  age: number;
  gender: string;
  avatarUrl?: string;
}

export interface CaseDoctor {
  id: string;
  name: string;
  specialty: string;
  avatarUrl?: string;
}

export interface CaseSummary {
  id: string;
  caseNumber: string;
  patient: CasePatient;
  chiefComplaint: string;
  primaryDiagnosis?: string;
  priority: CasePriority;
  status: CaseStatus;
  assignedTo: CaseDoctor;
  createdBy: CaseDoctor;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  symptomsCount: number;
  imagesCount: number;
  hasAISuggestions: boolean;
  isUnread?: boolean;
  lastActivity?: {
    action: string;
    by: string;
    at: string;
  };
}

export interface CaseListResponse {
  cases: CaseSummary[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// =============================================================================
// Filter Types
// =============================================================================

export interface CaseFilters {
  view: DashboardView;
  priority?: CasePriority[];
  status?: CaseStatus[];
  assignedTo?: string[];
  createdBy?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  search?: string;
}

export interface CaseSortOptions {
  field: "createdAt" | "updatedAt" | "priority" | "patientName";
  direction: "asc" | "desc";
}

// =============================================================================
// Dashboard Stats
// =============================================================================

export interface DashboardStats {
  activeCount: number;
  urgentCount: number;
  pendingReviewCount: number;
  completedToday: number;
  avgResolutionTime: number; // in hours
  totalThisWeek: number;
}

export interface FilterFacets {
  priorities: Array<{ value: CasePriority; count: number }>;
  statuses: Array<{ value: CaseStatus; count: number }>;
  doctors: Array<{ id: string; name: string; count: number }>;
}

// =============================================================================
// Bulk Actions
// =============================================================================

export type BulkAction =
  | "assign"
  | "archive"
  | "export"
  | "delete"
  | "change_priority"
  | "change_status";

export interface BulkActionPayload {
  caseIds: string[];
  action: BulkAction;
  targetDoctorId?: string;
  targetPriority?: CasePriority;
  targetStatus?: CaseStatus;
}

// =============================================================================
// Real-time Events
// =============================================================================

export type CaseEventType =
  | "case_created"
  | "case_updated"
  | "case_assigned"
  | "case_status_changed"
  | "case_priority_changed"
  | "case_completed"
  | "case_archived";

export interface CaseEvent {
  type: CaseEventType;
  caseId: string;
  caseNumber: string;
  data: Partial<CaseSummary>;
  triggeredBy: CaseDoctor;
  timestamp: string;
}

export interface CaseNotification {
  id: string;
  type: CaseEventType;
  title: string;
  message: string;
  caseId: string;
  caseNumber: string;
  read: boolean;
  createdAt: string;
}

// =============================================================================
// Drag & Drop
// =============================================================================

export interface DragItem {
  type: "case";
  caseId: string;
  currentAssignee: string;
}

export interface DropTarget {
  type: "doctor";
  doctorId: string;
  doctorName: string;
}
