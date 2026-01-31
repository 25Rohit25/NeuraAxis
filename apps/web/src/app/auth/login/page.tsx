"use client";

import { signIn } from "next-auth/react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";
  const error = searchParams.get("error");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [showMfa, setShowMfa] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage("");

    try {
      const result = await signIn("credentials", {
        email,
        password,
        mfaCode: showMfa ? mfaCode : undefined,
        redirect: false,
      });

      if (result?.error) {
        if (result.error === "MFARequired") {
          setShowMfa(true);
          setErrorMessage("");
        } else if (result.error === "AccountLocked") {
          setErrorMessage("Account locked. Please try again in 30 minutes.");
        } else {
          setErrorMessage(result.error);
        }
      } else if (result?.ok) {
        router.push(callbackUrl);
        router.refresh();
      }
    } catch (err) {
      setErrorMessage("An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center">
              <span className="text-white font-bold text-xl">N</span>
            </div>
            <span className="text-2xl font-bold text-white">NEURAXIS</span>
          </div>
          <p className="text-slate-400">
            AI-Powered Medical Diagnosis Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-8 shadow-2xl">
          <h1 className="text-2xl font-semibold text-white mb-2">
            Welcome back
          </h1>
          <p className="text-slate-400 mb-6">
            Sign in to access your dashboard
          </p>

          {/* Error Messages */}
          {(error || errorMessage) && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error === "CredentialsSignin"
                ? "Invalid email or password"
                : errorMessage || error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!showMfa ? (
              <>
                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="doctor@neuraxis.health"
                    required
                    autoComplete="email"
                    className="w-full px-4 py-3 rounded-lg bg-slate-900/50 border border-slate-600/50 text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                  />
                </div>

                {/* Password */}
                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-sm font-medium text-slate-300">
                      Password
                    </label>
                    <Link
                      href="/auth/forgot-password"
                      className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
                    >
                      Forgot password?
                    </Link>
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    autoComplete="current-password"
                    className="w-full px-4 py-3 rounded-lg bg-slate-900/50 border border-slate-600/50 text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                  />
                </div>
              </>
            ) : (
              /* MFA Code Input */
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Authentication Code
                </label>
                <p className="text-sm text-slate-400 mb-3">
                  Enter the 6-digit code from your authenticator app
                </p>
                <input
                  type="text"
                  value={mfaCode}
                  onChange={(e) =>
                    setMfaCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                  }
                  placeholder="000000"
                  required
                  autoComplete="one-time-code"
                  pattern="[0-9]{6}"
                  className="w-full px-4 py-3 rounded-lg bg-slate-900/50 border border-slate-600/50 text-white text-center text-2xl tracking-[0.5em] placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowMfa(false)}
                  className="mt-2 text-sm text-slate-400 hover:text-slate-300"
                >
                  ← Back to login
                </button>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  <span>{showMfa ? "Verifying..." : "Signing in..."}</span>
                </>
              ) : (
                <span>{showMfa ? "Verify Code" : "Sign In"}</span>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-slate-700" />
            <span className="text-sm text-slate-500">or continue with</span>
            <div className="flex-1 h-px bg-slate-700" />
          </div>

          {/* OAuth Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => signIn("google", { callbackUrl })}
              className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 border border-slate-600/50 text-slate-300 transition-all"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Google
            </button>
            <button
              onClick={() => signIn("azure-ad", { callbackUrl })}
              className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-slate-700/50 hover:bg-slate-700 border border-slate-600/50 text-slate-300 transition-all"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11.4 24H0V12.6L11.4 24zM24 24H12.6L24 12.6V24zM11.4 0H0v11.4L11.4 0zM24 0H12.6L24 11.4V0z" />
              </svg>
              Microsoft
            </button>
          </div>

          {/* Register Link */}
          <p className="mt-6 text-center text-slate-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/auth/register"
              className="text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              Create account
            </Link>
          </p>
        </div>

        {/* Security Notice */}
        <p className="mt-6 text-center text-xs text-slate-500">
          Protected by HIPAA-compliant security. Your data is encrypted.
        </p>
      </div>
    </div>
  );
}
