import { AppProviders } from "@/providers/AppProviders";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NEURAXIS - AI-Powered Medical Diagnosis",
  description:
    "Advanced AI platform for medical diagnosis and healthcare analytics",
  keywords: ["medical", "AI", "diagnosis", "healthcare", "analytics"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <AppProviders>
          <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
            {children}
          </div>
        </AppProviders>
      </body>
    </html>
  );
}
