"use client";

/**
 * NEURAXIS - Authentication Hooks
 * ================================
 * React hooks for authentication state and operations.
 */

import { signIn, signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";

export type UserRole =
  | "super_admin"
  | "admin"
  | "doctor"
  | "nurse"
  | "radiologist"
  | "technician"
  | "patient";

export interface AuthUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  role: UserRole;
  organizationId: string;
  permissions: string[];
  mfaEnabled: boolean;
}

export interface UseAuthReturn {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  accessToken: string | null;
  login: (
    email: string,
    password: string,
    mfaCode?: string
  ) => Promise<{ success: boolean; error?: string; mfaRequired?: boolean }>;
  logout: (callbackUrl?: string) => Promise<void>;
  hasRole: (...roles: UserRole[]) => boolean;
  hasPermission: (...permissions: string[]) => boolean;
  hasAnyPermission: (...permissions: string[]) => boolean;
}

/**
 * Main authentication hook
 */
export function useAuth(): UseAuthReturn {
  const { data: session, status } = useSession();
  const router = useRouter();

  const user = useMemo<AuthUser | null>(() => {
    if (!session?.user) return null;
    return {
      id: session.user.id,
      email: session.user.email,
      firstName: session.user.firstName,
      lastName: session.user.lastName,
      fullName: `${session.user.firstName} ${session.user.lastName}`,
      role: session.user.role as UserRole,
      organizationId: session.user.organizationId,
      permissions: session.user.permissions || [],
      mfaEnabled: session.user.mfaEnabled,
    };
  }, [session]);

  const login = useCallback(
    async (
      email: string,
      password: string,
      mfaCode?: string
    ): Promise<{ success: boolean; error?: string; mfaRequired?: boolean }> => {
      try {
        const result = await signIn("credentials", {
          email,
          password,
          mfaCode,
          redirect: false,
        });

        if (result?.error === "MFARequired") {
          return { success: false, mfaRequired: true };
        }

        if (result?.error) {
          return { success: false, error: result.error };
        }

        return { success: true };
      } catch (error) {
        return { success: false, error: "An unexpected error occurred" };
      }
    },
    []
  );

  const logout = useCallback(async (callbackUrl = "/auth/login") => {
    await signOut({ callbackUrl });
  }, []);

  const hasRole = useCallback(
    (...roles: UserRole[]): boolean => {
      if (!user) return false;
      return roles.includes(user.role);
    },
    [user]
  );

  const hasPermission = useCallback(
    (...permissions: string[]): boolean => {
      if (!user) return false;
      return permissions.every((p) => user.permissions.includes(p));
    },
    [user]
  );

  const hasAnyPermission = useCallback(
    (...permissions: string[]): boolean => {
      if (!user) return false;
      return permissions.some((p) => user.permissions.includes(p));
    },
    [user]
  );

  return {
    user,
    isAuthenticated: !!session?.user,
    isLoading: status === "loading",
    accessToken: session?.user?.accessToken || null,
    login,
    logout,
    hasRole,
    hasPermission,
    hasAnyPermission,
  };
}

/**
 * Hook to require authentication
 */
export function useRequireAuth(redirectUrl = "/auth/login") {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  if (!isLoading && !isAuthenticated) {
    router.push(redirectUrl);
  }

  return { user, isLoading };
}

/**
 * Hook to require specific role(s)
 */
export function useRequireRole(...roles: UserRole[]) {
  const { user, isLoading, hasRole } = useAuth();
  const router = useRouter();

  if (!isLoading && user && !hasRole(...roles)) {
    router.push("/unauthorized");
  }

  return { user, isLoading, hasAccess: hasRole(...roles) };
}

/**
 * Hook for protected API calls
 */
export function useProtectedFetch() {
  const { accessToken } = useAuth();

  const protectedFetch = useCallback(
    async (url: string, options: RequestInit = {}) => {
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const headers = new Headers(options.headers);
      headers.set("Authorization", `Bearer ${accessToken}`);

      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        // Token expired, trigger re-auth
        window.location.href = "/auth/login";
        throw new Error("Session expired");
      }

      return response;
    },
    [accessToken]
  );

  return protectedFetch;
}
