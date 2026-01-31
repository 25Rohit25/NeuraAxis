/**
 * NEURAXIS - Patient Profile Page
 * Comprehensive patient profile with all medical information
 */

"use client";

import { DashboardLayout, PageHeader } from "@/components/layout/Layout";
import {
  AllergiesList,
  ConditionsList,
} from "@/components/patients/profile/AllergiesConditions";
import {
  CareTeam,
  DocumentViewer,
} from "@/components/patients/profile/DocumentsCareTeam";
import { ImageGallery } from "@/components/patients/profile/ImageGallery";
import { LabResults } from "@/components/patients/profile/LabResults";
import { MedicationsList } from "@/components/patients/profile/MedicationsList";
import { Timeline } from "@/components/patients/profile/Timeline";
import { VitalsChart } from "@/components/patients/profile/VitalsChart";
import { Button } from "@/components/ui/Button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { useToast } from "@/components/ui/Toast";
import { cn, formatDate, formatPhoneNumber } from "@/lib/utils";
import type {
  EditPermissions,
  PatientProfileResponse,
} from "@/types/patient-profile";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

// Status badge styles
const STATUS_STYLES = {
  active: "bg-success/10 text-success border-success/30",
  inactive: "bg-muted text-muted-foreground border-muted-foreground/30",
  deceased: "bg-danger/10 text-danger border-danger/30",
  transferred: "bg-warning/10 text-warning border-warning/30",
};

export default function PatientProfilePage() {
  const params = useParams();
  const router = useRouter();
  const { success, error } = useToast();
  const patientId = params.id as string;

  // State
  const [data, setData] = useState<PatientProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [isEditing, setIsEditing] = useState(false);
  const [permissions, setPermissions] = useState<EditPermissions | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      ws = new WebSocket(`${wsUrl}/ws/patient/${patientId}`);

      ws.onopen = () => {
        console.log("WebSocket connected");
      };

      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        handleRealTimeUpdate(update);
      };

      ws.onclose = () => {
        // Reconnect after 5 seconds
        reconnectTimeout = setTimeout(connect, 5000);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        ws?.close();
      };
    };

    // Only connect if we have data
    if (data && !isLoading) {
      connect();
    }

    return () => {
      ws?.close();
      clearTimeout(reconnectTimeout);
    };
  }, [patientId, data, isLoading]);

  // Handle real-time updates
  const handleRealTimeUpdate = useCallback(
    (update: any) => {
      if (!data) return;

      switch (update.type) {
        case "vital_added":
          setData((prev) => {
            if (!prev) return prev;
            // Update vital trends
            return { ...prev, lastUpdated: new Date().toISOString() };
          });
          break;
        case "medication_changed":
          success("Update", "Medications updated");
          fetchProfile();
          break;
        case "note_added":
          setData((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              timeline: [update.data, ...prev.timeline],
              lastUpdated: new Date().toISOString(),
            };
          });
          break;
        default:
          fetchProfile();
      }
    },
    [data, success]
  );

  // Fetch patient profile
  const fetchProfile = useCallback(async () => {
    try {
      const response = await fetch(`/api/patients/${patientId}/profile`);
      if (!response.ok) {
        if (response.status === 403) {
          error(
            "Access Denied",
            "You do not have permission to view this patient"
          );
          router.push("/patients");
          return;
        }
        throw new Error("Failed to fetch profile");
      }
      const profileData = await response.json();
      setData(profileData);
      setPermissions(profileData.permissions || null);
    } catch (err) {
      console.error("Error fetching profile:", err);
      error("Error", "Failed to load patient profile");
    } finally {
      setIsLoading(false);
    }
  }, [patientId, error, router]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // Print handler
  const handlePrint = () => {
    window.print();
  };

  // Export to PDF
  const handleExportPDF = async () => {
    try {
      const response = await fetch(`/api/patients/${patientId}/export/pdf`, {
        method: "POST",
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `patient-${data?.profile.mrn || patientId}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        success("Export", "PDF downloaded successfully");
      }
    } catch (err) {
      error("Export Failed", "Failed to generate PDF");
    }
  };

  if (isLoading) {
    return <PatientProfileSkeleton />;
  }

  if (!data) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center h-96">
          <p className="text-muted-foreground mb-4">Patient not found</p>
          <Link href="/patients">
            <Button variant="outline">Back to Patients</Button>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  const {
    profile,
    timeline,
    medications,
    allergies,
    conditions,
    vitalTrends,
    labResults,
    images,
    documents,
    careTeam,
    hasEditAccess,
  } = data;

  return (
    <DashboardLayout>
      {/* Print styles */}
      <style jsx global>{`
        @media print {
          .no-print {
            display: none !important;
          }
          .print-break {
            page-break-before: always;
          }
          body {
            font-size: 12px;
          }
        }
      `}</style>

      <PageHeader
        title={profile.fullName}
        description={`MRN: ${profile.mrn}`}
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Patients", href: "/patients" },
          { label: profile.fullName },
        ]}
        actions={
          <div className="flex gap-2 no-print">
            <Button variant="outline" onClick={handlePrint}>
              <svg
                className="h-4 w-4 mr-2"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="6 9 6 2 18 2 18 9" />
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                <rect x="6" y="14" width="12" height="8" />
              </svg>
              Print
            </Button>
            <Button variant="outline" onClick={handleExportPDF}>
              <svg
                className="h-4 w-4 mr-2"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              Export PDF
            </Button>
            {hasEditAccess && (
              <Link href={`/patients/${patientId}/edit`}>
                <Button>Edit Patient</Button>
              </Link>
            )}
          </div>
        }
      />

      <div className="mt-6 space-y-6">
        {/* Patient Header Card */}
        <div className="p-6 rounded-xl border bg-card">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Photo and status */}
            <div className="flex flex-col items-center md:items-start">
              <div className="h-24 w-24 rounded-full bg-primary/10 text-primary flex items-center justify-center text-2xl font-bold mb-3">
                {profile.photoUrl ? (
                  <img
                    src={profile.photoUrl}
                    alt={profile.fullName}
                    className="h-full w-full rounded-full object-cover"
                  />
                ) : (
                  `${profile.firstName[0]}${profile.lastName[0]}`
                )}
              </div>
              <span
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-medium capitalize border",
                  STATUS_STYLES[profile.status]
                )}
              >
                {profile.status}
              </span>
            </div>

            {/* Demographics */}
            <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4">
              <InfoItem
                label="Date of Birth"
                value={formatDate(profile.dateOfBirth)}
              />
              <InfoItem label="Age" value={`${profile.age} years`} />
              <InfoItem label="Gender" value={profile.gender} />
              <InfoItem label="Blood Type" value={profile.bloodType || "—"} />
              <InfoItem
                label="Phone"
                value={formatPhoneNumber(profile.phonePrimary)}
              />
              <InfoItem label="Email" value={profile.email || "—"} />
              <InfoItem
                label="City"
                value={`${profile.city}, ${profile.state}`}
              />
              <InfoItem
                label="Last Visit"
                value={
                  profile.lastVisitDate
                    ? formatDate(profile.lastVisitDate)
                    : "None"
                }
              />
            </div>

            {/* Quick actions */}
            <div className="flex md:flex-col gap-2 no-print">
              <Button size="sm" variant="outline" className="gap-2">
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72" />
                </svg>
                Call
              </Button>
              <Button size="sm" variant="outline" className="gap-2">
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="2" y="4" width="20" height="16" rx="2" />
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                </svg>
                Email
              </Button>
              <Button size="sm" variant="outline" className="gap-2">
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
                Schedule
              </Button>
            </div>
          </div>

          {/* Emergency contact */}
          <div className="mt-4 pt-4 border-t flex flex-col md:flex-row gap-4 text-sm">
            <div className="flex items-center gap-2">
              <svg
                className="h-4 w-4 text-danger"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <span className="font-medium">Emergency Contact:</span>
              <span>
                {profile.emergencyContactName} (
                {profile.emergencyContactRelationship})
              </span>
              <span className="text-muted-foreground">
                {formatPhoneNumber(profile.emergencyContactPhone)}
              </span>
            </div>
            {profile.insuranceProvider && (
              <div className="flex items-center gap-2">
                <svg
                  className="h-4 w-4 text-muted-foreground"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                <span className="font-medium">Insurance:</span>
                <span>
                  {profile.insuranceProvider} (#{profile.insurancePolicyNumber})
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Tabs content */}
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="no-print"
        >
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="medications">Medications</TabsTrigger>
            <TabsTrigger value="vitals">Vitals</TabsTrigger>
            <TabsTrigger value="labs">Lab Results</TabsTrigger>
            <TabsTrigger value="imaging">Imaging</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left column */}
              <div className="lg:col-span-2 space-y-6">
                {/* Allergies & Conditions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-4 rounded-lg border bg-card">
                    <AllergiesList
                      allergies={allergies}
                      canEdit={hasEditAccess}
                    />
                  </div>
                  <div className="p-4 rounded-lg border bg-card">
                    <ConditionsList
                      conditions={conditions}
                      canEdit={hasEditAccess}
                    />
                  </div>
                </div>

                {/* Vitals chart */}
                <VitalsChart vitalTrends={vitalTrends} />

                {/* Recent timeline */}
                <div className="p-4 rounded-lg border bg-card">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold">Recent Activity</h3>
                    <button
                      onClick={() => setActiveTab("timeline")}
                      className="text-sm text-primary hover:underline"
                    >
                      View All
                    </button>
                  </div>
                  <Timeline events={timeline.slice(0, 5)} />
                </div>
              </div>

              {/* Right column */}
              <div className="space-y-6">
                {/* Care team */}
                <div className="p-4 rounded-lg border bg-card">
                  <CareTeam members={careTeam} canEdit={hasEditAccess} />
                </div>

                {/* Active medications */}
                <div className="p-4 rounded-lg border bg-card">
                  <h3 className="font-semibold text-sm mb-4 flex items-center gap-2">
                    Active Medications
                    <span className="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary">
                      {medications.filter((m) => m.status === "active").length}
                    </span>
                  </h3>
                  <MedicationsList
                    medications={medications
                      .filter((m) => m.status === "active")
                      .slice(0, 5)}
                    canEdit={hasEditAccess}
                  />
                  {medications.filter((m) => m.status === "active").length >
                    5 && (
                    <button
                      onClick={() => setActiveTab("medications")}
                      className="mt-3 text-sm text-primary hover:underline"
                    >
                      View all medications
                    </button>
                  )}
                </div>

                {/* Recent labs */}
                <div className="p-4 rounded-lg border bg-card">
                  <h3 className="font-semibold text-sm mb-4">
                    Recent Lab Results
                  </h3>
                  <LabResults labTests={labResults.slice(0, 3)} />
                  {labResults.length > 3 && (
                    <button
                      onClick={() => setActiveTab("labs")}
                      className="mt-3 text-sm text-primary hover:underline"
                    >
                      View all results
                    </button>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Timeline Tab */}
          <TabsContent value="timeline" className="mt-6">
            <div className="p-6 rounded-lg border bg-card">
              <Timeline events={timeline} />
            </div>
          </TabsContent>

          {/* Medications Tab */}
          <TabsContent value="medications" className="mt-6">
            <div className="p-6 rounded-lg border bg-card">
              <MedicationsList
                medications={medications}
                canEdit={hasEditAccess}
              />
            </div>
          </TabsContent>

          {/* Vitals Tab */}
          <TabsContent value="vitals" className="mt-6">
            <VitalsChart vitalTrends={vitalTrends} className="h-auto" />
          </TabsContent>

          {/* Labs Tab */}
          <TabsContent value="labs" className="mt-6">
            <div className="p-6 rounded-lg border bg-card">
              <LabResults labTests={labResults} />
            </div>
          </TabsContent>

          {/* Imaging Tab */}
          <TabsContent value="imaging" className="mt-6">
            <div className="p-6 rounded-lg border bg-card">
              <ImageGallery images={images} />
            </div>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents" className="mt-6">
            <div className="p-6 rounded-lg border bg-card">
              <DocumentViewer documents={documents} canUpload={hasEditAccess} />
            </div>
          </TabsContent>
        </Tabs>

        {/* Print view - shows all sections */}
        <div className="hidden print:block space-y-6">
          <div className="grid grid-cols-2 gap-6 print-break">
            <div>
              <h3 className="font-bold mb-4">Allergies</h3>
              <AllergiesList allergies={allergies} />
            </div>
            <div>
              <h3 className="font-bold mb-4">Chronic Conditions</h3>
              <ConditionsList conditions={conditions} />
            </div>
          </div>
          <div className="print-break">
            <h3 className="font-bold mb-4">Medications</h3>
            <MedicationsList medications={medications} />
          </div>
          <div className="print-break">
            <h3 className="font-bold mb-4">Care Team</h3>
            <CareTeam members={careTeam} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// Info item component
function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground mb-0.5">{label}</p>
      <p className="text-sm font-medium capitalize">{value}</p>
    </div>
  );
}

// Loading skeleton
function PatientProfileSkeleton() {
  return (
    <DashboardLayout>
      <div className="animate-pulse">
        <div className="h-8 w-48 bg-muted rounded mb-2" />
        <div className="h-4 w-32 bg-muted rounded mb-6" />

        <div className="p-6 rounded-xl border bg-card mb-6">
          <div className="flex gap-6">
            <div className="h-24 w-24 rounded-full bg-muted" />
            <div className="flex-1 grid grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i}>
                  <div className="h-3 w-16 bg-muted rounded mb-2" />
                  <div className="h-4 w-24 bg-muted rounded" />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="h-10 w-full max-w-lg bg-muted rounded mb-6" />

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 h-96 bg-muted rounded-lg" />
          <div className="h-96 bg-muted rounded-lg" />
        </div>
      </div>
    </DashboardLayout>
  );
}
