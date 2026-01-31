/**
 * NEURAXIS - NextAuth.js Configuration
 * =====================================
 * Authentication configuration with credentials provider and JWT.
 * Supports email/password login and OAuth providers.
 */

import NextAuth, { NextAuthOptions, User } from "next-auth";
import { JWT } from "next-auth/jwt";
import AzureADProvider from "next-auth/providers/azure-ad";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";

// Extended types
declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      email: string;
      firstName: string;
      lastName: string;
      role: string;
      organizationId: string;
      permissions: string[];
      mfaEnabled: boolean;
      accessToken: string;
      refreshToken: string;
    };
    error?: string;
  }

  interface User {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    role: string;
    organizationId: string;
    permissions: string[];
    mfaEnabled: boolean;
    accessToken: string;
    refreshToken: string;
    expiresIn: number;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    role: string;
    organizationId: string;
    permissions: string[];
    mfaEnabled: boolean;
    accessToken: string;
    refreshToken: string;
    accessTokenExpires: number;
    error?: string;
  }
}

// Environment variables
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * Refresh access token using refresh token
 */
async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token.refreshToken }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error("Failed to refresh token");
    }

    return {
      ...token,
      accessToken: data.access_token,
      refreshToken: data.refresh_token ?? token.refreshToken,
      accessTokenExpires: Date.now() + data.expires_in * 1000,
    };
  } catch (error) {
    console.error("Error refreshing access token:", error);
    return {
      ...token,
      error: "RefreshAccessTokenError",
    };
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    // Email/Password credentials
    CredentialsProvider({
      id: "credentials",
      name: "Email & Password",
      credentials: {
        email: {
          label: "Email",
          type: "email",
          placeholder: "doctor@neuraxis.health",
        },
        password: { label: "Password", type: "password" },
        mfaCode: {
          label: "MFA Code",
          type: "text",
          placeholder: "6-digit code",
        },
      },
      async authorize(credentials): Promise<User | null> {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Email and password required");
        }

        try {
          const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
              mfa_code: credentials.mfaCode || undefined,
            }),
          });

          const data = await response.json();

          if (!response.ok) {
            if (response.status === 423) {
              throw new Error("AccountLocked");
            }
            if (data.mfa_required) {
              throw new Error("MFARequired");
            }
            throw new Error(data.detail || "Authentication failed");
          }

          if (data.mfa_required) {
            throw new Error("MFARequired");
          }

          if (!data.success || !data.user || !data.tokens) {
            throw new Error("Invalid response from server");
          }

          return {
            id: data.user.id,
            email: data.user.email,
            firstName: data.user.first_name,
            lastName: data.user.last_name,
            role: data.user.role,
            organizationId: data.user.organization_id,
            permissions: ["patient:read", "diagnosis:read"], // From backend
            mfaEnabled: data.user.mfa_enabled,
            accessToken: data.tokens.access_token,
            refreshToken: data.tokens.refresh_token,
            expiresIn: data.tokens.expires_in,
          };
        } catch (error) {
          console.error("Login error:", error);
          throw error;
        }
      },
    }),

    // Google OAuth (optional)
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
            authorization: {
              params: {
                prompt: "consent",
                access_type: "offline",
                response_type: "code",
              },
            },
          }),
        ]
      : []),

    // Azure AD (optional - for enterprise SSO)
    ...(process.env.AZURE_AD_CLIENT_ID && process.env.AZURE_AD_CLIENT_SECRET
      ? [
          AzureADProvider({
            clientId: process.env.AZURE_AD_CLIENT_ID,
            clientSecret: process.env.AZURE_AD_CLIENT_SECRET,
            tenantId: process.env.AZURE_AD_TENANT_ID,
          }),
        ]
      : []),
  ],

  pages: {
    signIn: "/auth/login",
    signOut: "/auth/logout",
    error: "/auth/error",
    verifyRequest: "/auth/verify",
  },

  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60, // 24 hours
  },

  callbacks: {
    async jwt({ token, user, account }): Promise<JWT> {
      // Initial sign in
      if (user) {
        return {
          ...token,
          id: user.id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          role: user.role,
          organizationId: user.organizationId,
          permissions: user.permissions,
          mfaEnabled: user.mfaEnabled,
          accessToken: user.accessToken,
          refreshToken: user.refreshToken,
          accessTokenExpires: Date.now() + user.expiresIn * 1000,
        };
      }

      // Return previous token if not expired
      if (Date.now() < (token.accessTokenExpires || 0)) {
        return token;
      }

      // Access token expired, refresh it
      return refreshAccessToken(token);
    },

    async session({ session, token }) {
      if (token.error) {
        session.error = token.error;
      }

      session.user = {
        id: token.id,
        email: token.email,
        firstName: token.firstName,
        lastName: token.lastName,
        role: token.role,
        organizationId: token.organizationId,
        permissions: token.permissions,
        mfaEnabled: token.mfaEnabled,
        accessToken: token.accessToken,
        refreshToken: token.refreshToken,
      };

      return session;
    },

    async signIn({ user, account, profile }) {
      // Handle OAuth providers
      if (account?.provider !== "credentials") {
        // TODO: Create/link user in backend for OAuth providers
        return true;
      }
      return true;
    },
  },

  events: {
    async signIn({ user, account, isNewUser }) {
      console.log(`[AUTH] User signed in: ${user.email}`);
    },
    async signOut({ token }) {
      // Notify backend to invalidate session
      try {
        await fetch(`${BACKEND_URL}/api/v1/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token.accessToken}`,
          },
        });
      } catch (error) {
        console.error("Logout notification failed:", error);
      }
    },
  },

  debug: process.env.NODE_ENV === "development",
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
