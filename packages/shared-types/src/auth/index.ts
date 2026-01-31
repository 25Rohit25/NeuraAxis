// ============================================================================
// NEURAXIS - Authentication & Authorization Types
// ============================================================================
// TypeScript types for the authentication system
// HIPAA-compliant with role-based access control
// ============================================================================

import { OrganizationId, UserId } from "../common";

// ============================================================================
// USER ROLES
// ============================================================================

/**
 * User roles with hierarchical permissions
 * super_admin > admin > doctor > nurse > radiologist > technician > patient
 */
export enum UserRole {
  SUPER_ADMIN = "super_admin",
  ADMIN = "admin",
  DOCTOR = "doctor",
  NURSE = "nurse",
  RADIOLOGIST = "radiologist",
  TECHNICIAN = "technician",
  PATIENT = "patient",
}

/**
 * Role hierarchy for permission inheritance
 */
export const ROLE_HIERARCHY: Record<UserRole, number> = {
  [UserRole.SUPER_ADMIN]: 100,
  [UserRole.ADMIN]: 80,
  [UserRole.DOCTOR]: 60,
  [UserRole.RADIOLOGIST]: 55,
  [UserRole.NURSE]: 50,
  [UserRole.TECHNICIAN]: 40,
  [UserRole.PATIENT]: 10,
};

/**
 * Check if a role has higher or equal privilege than another
 */
export function hasRolePrivilege(
  userRole: UserRole,
  requiredRole: UserRole
): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

// ============================================================================
// USER STATUS
// ============================================================================

export enum UserStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  SUSPENDED = "suspended",
  PENDING_VERIFICATION = "pending_verification",
  LOCKED = "locked",
}

// ============================================================================
// AUTHENTICATION TYPES
// ============================================================================

/**
 * Login request payload
 */
export interface LoginRequest {
  email: string;
  password: string;
  mfaCode?: string;
  rememberMe?: boolean;
}

/**
 * Registration request payload
 */
export interface RegisterRequest {
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  organizationId?: string;
  role?: UserRole;
  acceptedTerms: boolean;
}

/**
 * Password reset request
 */
export interface PasswordResetRequest {
  email: string;
}

/**
 * Password reset confirmation
 */
export interface PasswordResetConfirmRequest {
  token: string;
  newPassword: string;
  confirmPassword: string;
}

/**
 * Change password request
 */
export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

// ============================================================================
// MFA TYPES
// ============================================================================

export enum MFAMethod {
  TOTP = "totp",
  SMS = "sms",
  EMAIL = "email",
}

/**
 * MFA setup response
 */
export interface MFASetupResponse {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
}

/**
 * MFA verification request
 */
export interface MFAVerifyRequest {
  code: string;
  method?: MFAMethod;
}

/**
 * MFA status
 */
export interface MFAStatus {
  enabled: boolean;
  method: MFAMethod | null;
  verifiedAt: string | null;
}

// ============================================================================
// SESSION & TOKEN TYPES
// ============================================================================

/**
 * JWT access token payload
 */
export interface AccessTokenPayload {
  sub: UserId;
  email: string;
  role: UserRole;
  organizationId: OrganizationId;
  permissions: string[];
  sessionId: string;
  iat: number;
  exp: number;
  type: "access";
}

/**
 * JWT refresh token payload
 */
export interface RefreshTokenPayload {
  sub: UserId;
  sessionId: string;
  iat: number;
  exp: number;
  type: "refresh";
}

/**
 * Token pair response
 */
export interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: "Bearer";
}

/**
 * Session information
 */
export interface SessionInfo {
  id: string;
  userId: UserId;
  organizationId: OrganizationId;
  ipAddress: string;
  userAgent: string;
  createdAt: string;
  lastActivityAt: string;
  expiresAt: string;
  isCurrentSession: boolean;
}

// ============================================================================
// USER TYPES
// ============================================================================

/**
 * Authenticated user (session user)
 */
export interface AuthUser {
  id: UserId;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  role: UserRole;
  status: UserStatus;
  organizationId: OrganizationId;
  organizationName: string;
  permissions: string[];
  mfaEnabled: boolean;
  avatarUrl?: string;
  lastLoginAt?: string;
}

/**
 * Full user profile
 */
export interface UserProfile extends AuthUser {
  title?: string;
  specialization?: string;
  licenseNumber?: string;
  licenseState?: string;
  licenseExpiry?: string;
  npiNumber?: string;
  phone?: string;
  phoneExtension?: string;
  mustChangePassword: boolean;
  passwordChangedAt?: string;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// AUTH RESPONSE TYPES
// ============================================================================

/**
 * Login response
 */
export interface LoginResponse {
  success: boolean;
  user?: AuthUser;
  tokens?: TokenPair;
  mfaRequired?: boolean;
  mfaMethod?: MFAMethod;
  sessionId?: string;
  message?: string;
}

/**
 * Logout response
 */
export interface LogoutResponse {
  success: boolean;
  message: string;
}

/**
 * Token refresh response
 */
export interface RefreshTokenResponse {
  success: boolean;
  tokens?: TokenPair;
  message?: string;
}

// ============================================================================
// PERMISSION TYPES
// ============================================================================

/**
 * Resource types for RBAC
 */
export enum ResourceType {
  PATIENT = "patient",
  MEDICAL_CASE = "medical_case",
  DIAGNOSIS = "diagnosis",
  MEDICAL_IMAGE = "medical_image",
  TREATMENT_PLAN = "treatment_plan",
  USER = "user",
  ORGANIZATION = "organization",
  AUDIT_LOG = "audit_log",
  REPORT = "report",
  SETTINGS = "settings",
}

/**
 * Actions for RBAC
 */
export enum Action {
  CREATE = "create",
  READ = "read",
  UPDATE = "update",
  DELETE = "delete",
  EXPORT = "export",
  SHARE = "share",
  APPROVE = "approve",
  ASSIGN = "assign",
}

/**
 * Permission string format: "resource:action"
 */
export type Permission = `${ResourceType}:${Action}`;

/**
 * Role permissions mapping
 */
export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  [UserRole.SUPER_ADMIN]: [
    // Full access to everything
    "patient:create",
    "patient:read",
    "patient:update",
    "patient:delete",
    "patient:export",
    "medical_case:create",
    "medical_case:read",
    "medical_case:update",
    "medical_case:delete",
    "medical_case:assign",
    "diagnosis:create",
    "diagnosis:read",
    "diagnosis:update",
    "diagnosis:delete",
    "diagnosis:approve",
    "medical_image:create",
    "medical_image:read",
    "medical_image:update",
    "medical_image:delete",
    "treatment_plan:create",
    "treatment_plan:read",
    "treatment_plan:update",
    "treatment_plan:delete",
    "treatment_plan:approve",
    "user:create",
    "user:read",
    "user:update",
    "user:delete",
    "organization:create",
    "organization:read",
    "organization:update",
    "organization:delete",
    "audit_log:read",
    "audit_log:export",
    "report:read",
    "report:create",
    "report:export",
    "settings:read",
    "settings:update",
  ],
  [UserRole.ADMIN]: [
    "patient:create",
    "patient:read",
    "patient:update",
    "patient:export",
    "medical_case:create",
    "medical_case:read",
    "medical_case:update",
    "medical_case:assign",
    "diagnosis:create",
    "diagnosis:read",
    "diagnosis:update",
    "diagnosis:approve",
    "medical_image:create",
    "medical_image:read",
    "medical_image:update",
    "treatment_plan:create",
    "treatment_plan:read",
    "treatment_plan:update",
    "treatment_plan:approve",
    "user:create",
    "user:read",
    "user:update",
    "organization:read",
    "organization:update",
    "audit_log:read",
    "report:read",
    "report:create",
    "settings:read",
    "settings:update",
  ],
  [UserRole.DOCTOR]: [
    "patient:create",
    "patient:read",
    "patient:update",
    "medical_case:create",
    "medical_case:read",
    "medical_case:update",
    "diagnosis:create",
    "diagnosis:read",
    "diagnosis:update",
    "diagnosis:approve",
    "medical_image:read",
    "medical_image:update",
    "treatment_plan:create",
    "treatment_plan:read",
    "treatment_plan:update",
    "treatment_plan:approve",
    "report:read",
    "report:create",
  ],
  [UserRole.RADIOLOGIST]: [
    "patient:read",
    "medical_case:read",
    "diagnosis:create",
    "diagnosis:read",
    "diagnosis:update",
    "medical_image:read",
    "medical_image:update",
    "report:read",
    "report:create",
  ],
  [UserRole.NURSE]: [
    "patient:read",
    "patient:update",
    "medical_case:read",
    "medical_case:update",
    "diagnosis:read",
    "medical_image:read",
    "treatment_plan:read",
    "report:read",
  ],
  [UserRole.TECHNICIAN]: [
    "patient:read",
    "medical_case:read",
    "medical_image:create",
    "medical_image:read",
    "medical_image:update",
  ],
  [UserRole.PATIENT]: [
    "patient:read", // Own record only
    "medical_case:read", // Own cases only
    "diagnosis:read", // Own diagnoses only
    "medical_image:read", // Own images only
    "treatment_plan:read", // Own treatment plans only
  ],
};

/**
 * Check if a role has a specific permission
 */
export function hasPermission(role: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

/**
 * Get all permissions for a role
 */
export function getRolePermissions(role: UserRole): Permission[] {
  return ROLE_PERMISSIONS[role] ?? [];
}

// ============================================================================
// AUDIT TYPES
// ============================================================================

export enum AuthEventType {
  LOGIN_SUCCESS = "login_success",
  LOGIN_FAILED = "login_failed",
  LOGOUT = "logout",
  PASSWORD_CHANGED = "password_changed",
  PASSWORD_RESET_REQUESTED = "password_reset_requested",
  PASSWORD_RESET_COMPLETED = "password_reset_completed",
  MFA_ENABLED = "mfa_enabled",
  MFA_DISABLED = "mfa_disabled",
  MFA_VERIFIED = "mfa_verified",
  MFA_FAILED = "mfa_failed",
  ACCOUNT_LOCKED = "account_locked",
  ACCOUNT_UNLOCKED = "account_unlocked",
  SESSION_CREATED = "session_created",
  SESSION_EXPIRED = "session_expired",
  SESSION_REVOKED = "session_revoked",
  TOKEN_REFRESHED = "token_refreshed",
  SUSPICIOUS_ACTIVITY = "suspicious_activity",
}

/**
 * Auth audit event
 */
export interface AuthAuditEvent {
  id: string;
  userId?: UserId;
  email?: string;
  eventType: AuthEventType;
  ipAddress: string;
  userAgent: string;
  success: boolean;
  errorMessage?: string;
  metadata?: Record<string, unknown>;
  createdAt: string;
}

// ============================================================================
// SECURITY TYPES
// ============================================================================

/**
 * Account lockout status
 */
export interface LockoutStatus {
  isLocked: boolean;
  failedAttempts: number;
  lockedUntil?: string;
  remainingLockoutTime?: number; // seconds
}

/**
 * Password validation result
 */
export interface PasswordValidationResult {
  isValid: boolean;
  errors: string[];
  strength: "weak" | "fair" | "good" | "strong" | "very_strong";
  score: number; // 0-100
}

/**
 * Password requirements
 */
export interface PasswordRequirements {
  minLength: number;
  maxLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  preventCommonPasswords: boolean;
  preventUserInfoInPassword: boolean;
}

export const DEFAULT_PASSWORD_REQUIREMENTS: PasswordRequirements = {
  minLength: 12,
  maxLength: 128,
  requireUppercase: true,
  requireLowercase: true,
  requireNumbers: true,
  requireSpecialChars: true,
  preventCommonPasswords: true,
  preventUserInfoInPassword: true,
};
