/**
 * NEURAXIS - Patient Registration Page
 * New patient registration with multi-step wizard
 */

"use client";

import { DashboardLayout, PageHeader } from "@/components/layout/Layout";
import { PatientRegistrationForm } from "@/components/patients/RegistrationForm";
import { useToast } from "@/components/ui/Toast";
import { useRouter } from "next/navigation";

export default function NewPatientPage() {
  const router = useRouter();
  const { success } = useToast();

  const handleSuccess = (result: { id: string; mrn: string }) => {
    success(
      "Patient Registered",
      `Patient registered successfully. MRN: ${result.mrn}`
    );
    router.push(`/patients/${result.id}`);
  };

  const handleCancel = () => {
    router.back();
  };

  return (
    <DashboardLayout>
      <PageHeader
        title="Register New Patient"
        description="Enter patient demographics, medical history, and emergency contact information"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Patients", href: "/patients" },
          { label: "New Registration" },
        ]}
      />

      <div className="mt-6">
        <PatientRegistrationForm
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      </div>
    </DashboardLayout>
  );
}
