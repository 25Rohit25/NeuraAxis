/**
 * NEURAXIS - Patient Search Types
 * TypeScript types for patient search, filtering, and pagination
 */

// =============================================================================
// Enums
// =============================================================================

export type PatientStatus = "active" | "inactive" | "deceased" | "transferred";
export type Gender = "male" | "female" | "other" | "prefer_not_to_say";
export type SortField =
  | "name"
  | "mrn"
  | "dateOfBirth"
  | "lastVisit"
  | "createdAt";
export type SortDirection = "asc" | "desc";

// =============================================================================
// Search Parameters
// =============================================================================

export interface PatientSearchParams {
  // Text search
  query?: string;

  // Filters
  status?: PatientStatus | PatientStatus[];
  gender?: Gender | Gender[];
  ageMin?: number;
  ageMax?: number;
  conditions?: string[];
  hasAllergies?: boolean;

  // Date filters
  createdAfter?: string;
  createdBefore?: string;
  lastVisitAfter?: string;
  lastVisitBefore?: string;

  // Sorting
  sortBy?: SortField;
  sortDirection?: SortDirection;

  // Pagination
  page?: number;
  pageSize?: number;
}

export interface PatientSearchFilters {
  status: PatientStatus[];
  gender: Gender[];
  ageRange: [number | null, number | null];
  conditions: string[];
  hasAllergies: boolean | null;
  dateRange: {
    createdAfter: string | null;
    createdBefore: string | null;
  };
}

// =============================================================================
// Patient List Item
// =============================================================================

export interface PatientListItem {
  id: string;
  mrn: string;
  firstName: string;
  lastName: string;
  fullName: string;
  dateOfBirth: string;
  age: number;
  gender: Gender;
  phonePrimary: string;
  email: string | null;
  city: string;
  state: string;
  status: PatientStatus;
  primaryDiagnosis: string | null;
  allergiesCount: number;
  conditionsCount: number;
  lastVisitDate: string | null;
  createdAt: string;
  updatedAt: string;
}

// =============================================================================
// Paginated Response
// =============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

export type PatientListResponse = PaginatedResponse<PatientListItem>;

// =============================================================================
// Search Facets (for filter counts)
// =============================================================================

export interface SearchFacets {
  status: Record<PatientStatus, number>;
  gender: Record<Gender, number>;
  ageRanges: {
    "0-17": number;
    "18-30": number;
    "31-50": number;
    "51-70": number;
    "71+": number;
  };
  topConditions: Array<{ condition: string; count: number }>;
}

// =============================================================================
// Bulk Actions
// =============================================================================

export type BulkAction = "export" | "archive" | "activate" | "delete";

export interface BulkActionRequest {
  action: BulkAction;
  patientIds: string[];
}

export interface BulkActionResult {
  success: boolean;
  processedCount: number;
  failedCount: number;
  errors?: string[];
}

// =============================================================================
// Export Options
// =============================================================================

export type ExportFormat = "csv" | "xlsx" | "pdf";

export interface ExportOptions {
  format: ExportFormat;
  fields?: string[];
  includeContactInfo?: boolean;
  includeMedicalInfo?: boolean;
}

// =============================================================================
// Quick Filters (Presets)
// =============================================================================

export interface QuickFilter {
  id: string;
  label: string;
  icon?: string;
  params: Partial<PatientSearchParams>;
}

export const QUICK_FILTERS: QuickFilter[] = [
  {
    id: "all",
    label: "All Patients",
    params: {},
  },
  {
    id: "active",
    label: "Active",
    params: { status: "active" },
  },
  {
    id: "recent",
    label: "Recent (7 days)",
    params: {
      createdAfter: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0],
    },
  },
  {
    id: "elderly",
    label: "Elderly (65+)",
    params: { ageMin: 65 },
  },
  {
    id: "pediatric",
    label: "Pediatric (0-17)",
    params: { ageMax: 17 },
  },
  {
    id: "with-allergies",
    label: "Has Allergies",
    params: { hasAllergies: true },
  },
];

// =============================================================================
// Column Definition for Table
// =============================================================================

export interface PatientTableColumn {
  key: keyof PatientListItem | "actions" | "select";
  label: string;
  sortable?: boolean;
  width?: string;
  align?: "left" | "center" | "right";
  visible?: boolean;
}

export const DEFAULT_COLUMNS: PatientTableColumn[] = [
  { key: "select", label: "", width: "40px", align: "center" },
  { key: "mrn", label: "MRN", sortable: true, width: "120px" },
  { key: "fullName", label: "Patient Name", sortable: true },
  { key: "age", label: "Age", sortable: true, width: "60px", align: "center" },
  { key: "gender", label: "Gender", width: "80px" },
  { key: "phonePrimary", label: "Phone", width: "130px" },
  { key: "status", label: "Status", width: "100px" },
  { key: "lastVisitDate", label: "Last Visit", sortable: true, width: "110px" },
  { key: "createdAt", label: "Registered", sortable: true, width: "110px" },
  { key: "actions", label: "", width: "80px", align: "right" },
];

// =============================================================================
// Utility Functions
// =============================================================================

export function buildSearchParams(
  filters: Partial<PatientSearchFilters>
): PatientSearchParams {
  const params: PatientSearchParams = {};

  if (filters.status?.length) {
    params.status = filters.status;
  }
  if (filters.gender?.length) {
    params.gender = filters.gender;
  }
  if (filters.ageRange?.[0] != null) {
    params.ageMin = filters.ageRange[0];
  }
  if (filters.ageRange?.[1] != null) {
    params.ageMax = filters.ageRange[1];
  }
  if (filters.conditions?.length) {
    params.conditions = filters.conditions;
  }
  if (filters.hasAllergies != null) {
    params.hasAllergies = filters.hasAllergies;
  }
  if (filters.dateRange?.createdAfter) {
    params.createdAfter = filters.dateRange.createdAfter;
  }
  if (filters.dateRange?.createdBefore) {
    params.createdBefore = filters.dateRange.createdBefore;
  }

  return params;
}

export function parseSearchParams(
  searchParams: URLSearchParams
): PatientSearchParams {
  const params: PatientSearchParams = {};

  const query = searchParams.get("q");
  if (query) params.query = query;

  const status = searchParams.getAll("status");
  if (status.length) params.status = status as PatientStatus[];

  const gender = searchParams.getAll("gender");
  if (gender.length) params.gender = gender as Gender[];

  const ageMin = searchParams.get("ageMin");
  if (ageMin) params.ageMin = parseInt(ageMin, 10);

  const ageMax = searchParams.get("ageMax");
  if (ageMax) params.ageMax = parseInt(ageMax, 10);

  const sortBy = searchParams.get("sortBy");
  if (sortBy) params.sortBy = sortBy as SortField;

  const sortDirection = searchParams.get("sortDirection");
  if (sortDirection) params.sortDirection = sortDirection as SortDirection;

  const page = searchParams.get("page");
  params.page = page ? parseInt(page, 10) : 1;

  const pageSize = searchParams.get("pageSize");
  params.pageSize = pageSize ? parseInt(pageSize, 10) : 20;

  return params;
}

export function serializeSearchParams(params: PatientSearchParams): string {
  const urlParams = new URLSearchParams();

  if (params.query) urlParams.set("q", params.query);

  if (Array.isArray(params.status)) {
    params.status.forEach((s) => urlParams.append("status", s));
  } else if (params.status) {
    urlParams.set("status", params.status);
  }

  if (Array.isArray(params.gender)) {
    params.gender.forEach((g) => urlParams.append("gender", g));
  } else if (params.gender) {
    urlParams.set("gender", params.gender);
  }

  if (params.ageMin != null) urlParams.set("ageMin", params.ageMin.toString());
  if (params.ageMax != null) urlParams.set("ageMax", params.ageMax.toString());
  if (params.sortBy) urlParams.set("sortBy", params.sortBy);
  if (params.sortDirection)
    urlParams.set("sortDirection", params.sortDirection);
  if (params.page) urlParams.set("page", params.page.toString());
  if (params.pageSize) urlParams.set("pageSize", params.pageSize.toString());

  return urlParams.toString();
}
