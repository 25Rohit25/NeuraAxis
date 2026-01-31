// ============================================
// API Types
// ============================================

import { Timestamp } from "../common";

/** Standard API response wrapper */
export interface ApiResponse<T> {
    success: boolean;
    data: T;
    message?: string;
    timestamp: Timestamp;
}

/** Paginated response wrapper */
export interface PaginatedResponse<T> {
    success: boolean;
    data: T[];
    pagination: PaginationMeta;
    timestamp: Timestamp;
}

/** Pagination metadata */
export interface PaginationMeta {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNextPage: boolean;
    hasPreviousPage: boolean;
}

/** API error response */
export interface ErrorResponse {
    success: false;
    error: {
        code: string;
        message: string;
        details?: Record<string, unknown>;
        stack?: string;
    };
    timestamp: Timestamp;
}

/** Health check response */
export interface HealthCheckResponse {
    status: "healthy" | "degraded" | "unhealthy";
    version: string;
    uptime: number;
    checks: HealthCheck[];
}

/** Individual health check */
export interface HealthCheck {
    name: string;
    status: "pass" | "warn" | "fail";
    responseTime?: number;
    message?: string;
}

/** Authentication request */
export interface LoginRequest {
    email: string;
    password: string;
}

/** Authentication response */
export interface AuthResponse {
    accessToken: string;
    refreshToken: string;
    expiresIn: number;
    tokenType: "Bearer";
}

/** Diagnosis request */
export interface CreateDiagnosisRequest {
    patientId: string;
    symptoms: string[];
    medicalHistory?: string;
    imageIds?: string[];
    notes?: string;
}

/** Image upload response */
export interface ImageUploadResponse {
    id: string;
    url: string;
    thumbnailUrl: string;
    analysisStatus: "pending" | "processing" | "completed" | "failed";
}

/** WebSocket message types */
export enum WebSocketMessageType {
    DIAGNOSIS_UPDATE = "diagnosis_update",
    IMAGE_ANALYSIS_COMPLETE = "image_analysis_complete",
    NOTIFICATION = "notification",
    HEARTBEAT = "heartbeat",
}

/** WebSocket message */
export interface WebSocketMessage<T = unknown> {
    type: WebSocketMessageType;
    payload: T;
    timestamp: Timestamp;
}
