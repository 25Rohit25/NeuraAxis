// ============================================
// Common Types
// ============================================

/** Branded type for type-safe IDs */
export type ID<T extends string = string> = string & { readonly __brand: T };

/** Patient ID */
export type PatientId = ID<"Patient">;

/** Diagnosis ID */
export type DiagnosisId = ID<"Diagnosis">;

/** User ID */
export type UserId = ID<"User">;

/** Organization ID */
export type OrganizationId = ID<"Organization">;

/** Timestamp in ISO 8601 format */
export type Timestamp = string;

/** Sort order enum */
export enum SortOrder {
    ASC = "asc",
    DESC = "desc",
}

/** Pagination parameters */
export interface PaginationParams {
    page: number;
    limit: number;
    sortBy?: string;
    sortOrder?: SortOrder;
}

/** Nullable type helper */
export type Nullable<T> = T | null;

/** Optional type helper */
export type Optional<T> = T | undefined;

/** Deep partial type helper */
export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
