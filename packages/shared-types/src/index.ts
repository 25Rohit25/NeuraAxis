// ============================================
// @neuraxis/shared-types - Main Exports
// ============================================

// Common types
export * from "./common";

// Model types
export * from "./models";

// API types
export * from "./api";

// Auth types - exported with aliases to avoid conflicts
// Note: Use import from "./auth" directly if you need the original names
export type {
  AccessTokenPayload,
  Action,
  AuthAuditEvent,
  AuthEventType,
  LoginRequest as AuthLoginRequest,
  AuthUser,
  // Types renamed to avoid conflicts
  UserRole as AuthUserRole,
  UserStatus as AuthUserStatus,
  ChangePasswordRequest,
  LockoutStatus,
  LoginResponse,
  LogoutResponse,
  MFAMethod,
  MFASetupResponse,
  MFAStatus,
  MFAVerifyRequest,
  PasswordRequirements,
  PasswordResetConfirmRequest,
  PasswordResetRequest,
  PasswordValidationResult,
  Permission,
  RefreshTokenPayload,
  RefreshTokenResponse,
  // Unique types
  RegisterRequest,
  ResourceType,
  SessionInfo,
  TokenPair,
  UserProfile,
} from "./auth";

// Re-export runtime values
export {
  DEFAULT_PASSWORD_REQUIREMENTS,
  ROLE_HIERARCHY,
  ROLE_PERMISSIONS,
  getRolePermissions,
  hasPermission,
  hasRolePrivilege,
} from "./auth";
