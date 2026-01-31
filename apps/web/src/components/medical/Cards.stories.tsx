import type { Meta, StoryObj } from "@storybook/react";
import type { TimelineEvent } from "./Cards";
import { CaseCard, DiagnosisCard, PatientCard, TimelineCard } from "./Cards";

// Patient Card Stories
const PatientCardMeta: Meta<typeof PatientCard> = {
  title: "Medical/PatientCard",
  component: PatientCard,
  tags: ["autodocs"],
  argTypes: {
    status: {
      control: "select",
      options: ["active", "discharged", "critical", "stable"],
    },
    gender: {
      control: "select",
      options: ["male", "female", "other"],
    },
  },
};

export default PatientCardMeta;
type PatientCardStory = StoryObj<typeof PatientCard>;

export const ActivePatient: PatientCardStory = {
  args: {
    id: "1",
    firstName: "Sarah",
    lastName: "Johnson",
    mrn: "MRN-2024-001234",
    dateOfBirth: "1985-03-15",
    gender: "female",
    status: "active",
    lastVisit: "Jan 28, 2026",
    primaryDiagnosis: "Type 2 Diabetes Mellitus",
  },
};

export const CriticalPatient: PatientCardStory = {
  args: {
    id: "2",
    firstName: "James",
    lastName: "Wilson",
    mrn: "MRN-2024-005678",
    dateOfBirth: "1972-08-22",
    gender: "male",
    status: "critical",
    lastVisit: "Jan 29, 2026",
    primaryDiagnosis: "Acute Myocardial Infarction",
  },
};

export const DischargedPatient: PatientCardStory = {
  args: {
    id: "3",
    firstName: "Emily",
    lastName: "Chen",
    mrn: "MRN-2024-009012",
    dateOfBirth: "1990-11-30",
    gender: "female",
    status: "discharged",
    lastVisit: "Jan 20, 2026",
    primaryDiagnosis: "Post-operative care - Appendectomy",
  },
};

export const ClickablePatient: PatientCardStory = {
  args: {
    id: "4",
    firstName: "Michael",
    lastName: "Brown",
    mrn: "MRN-2024-003456",
    dateOfBirth: "1968-05-10",
    gender: "male",
    status: "stable",
    lastVisit: "Jan 25, 2026",
    primaryDiagnosis: "Hypertension, well-controlled",
    onClick: () => alert("Patient card clicked!"),
  },
};

// Case Card stories
export const CaseCardStory: StoryObj<typeof CaseCard> = {
  render: () => (
    <div className="space-y-4 max-w-lg">
      <CaseCard
        id="1"
        patientName="Sarah Johnson"
        caseNumber="2026-0129-001"
        status="open"
        priority="urgent"
        chiefComplaint="Severe chest pain radiating to left arm, shortness of breath, diaphoresis for 2 hours"
        createdAt="Today at 2:30 PM"
        assignedTo="Dr. Smith"
      />
      <CaseCard
        id="2"
        patientName="James Wilson"
        caseNumber="2026-0129-002"
        status="in_progress"
        priority="high"
        chiefComplaint="Persistent headache with visual disturbances"
        createdAt="Today at 11:15 AM"
        assignedTo="Dr. Chen"
      />
      <CaseCard
        id="3"
        patientName="Emily Chen"
        caseNumber="2026-0128-015"
        status="pending_review"
        priority="medium"
        chiefComplaint="Follow-up for post-operative wound care"
        createdAt="Yesterday"
      />
      <CaseCard
        id="4"
        patientName="Michael Brown"
        caseNumber="2026-0127-008"
        status="closed"
        priority="low"
        chiefComplaint="Annual wellness check - completed"
        createdAt="2 days ago"
        assignedTo="Dr. Williams"
      />
    </div>
  ),
};

// Diagnosis Card stories
export const DiagnosisCardStory: StoryObj<typeof DiagnosisCard> = {
  render: () => (
    <div className="grid gap-4 md:grid-cols-2 max-w-3xl">
      <DiagnosisCard
        id="1"
        condition="Acute Myocardial Infarction (STEMI)"
        icdCode="I21.0"
        confidence={94}
        severity="critical"
        differentials={[
          "Unstable Angina",
          "Aortic Dissection",
          "Pulmonary Embolism",
        ]}
        aiGenerated
        createdAt="2 hours ago"
      />
      <DiagnosisCard
        id="2"
        condition="Type 2 Diabetes Mellitus"
        icdCode="E11.9"
        confidence={87}
        severity="moderate"
        differentials={["Type 1 Diabetes", "MODY", "Gestational Diabetes"]}
        aiGenerated
        verifiedBy="Dr. Chen"
        createdAt="Yesterday"
      />
      <DiagnosisCard
        id="3"
        condition="Essential Hypertension"
        icdCode="I10"
        confidence={72}
        severity="mild"
        aiGenerated
        createdAt="3 days ago"
      />
      <DiagnosisCard
        id="4"
        condition="Common Cold (Acute Nasopharyngitis)"
        icdCode="J00"
        confidence={55}
        severity="minimal"
        differentials={[
          "Influenza",
          "COVID-19",
          "Allergic Rhinitis",
          "Sinusitis",
          "Strep Throat",
        ]}
        aiGenerated
        createdAt="1 week ago"
      />
    </div>
  ),
};

// Timeline Card stories
const sampleEvents: TimelineEvent[] = [
  {
    id: "1",
    type: "visit",
    title: "Emergency Department Visit",
    description: "Presented with chest pain and shortness of breath",
    date: "Jan 29, 2026 - 2:30 PM",
    provider: "Dr. Smith",
  },
  {
    id: "2",
    type: "diagnosis",
    title: "Diagnosis: Acute MI (STEMI)",
    description: "Confirmed via ECG and troponin levels",
    date: "Jan 29, 2026 - 3:15 PM",
    provider: "Dr. Chen",
  },
  {
    id: "3",
    type: "imaging",
    title: "Cardiac Catheterization",
    description: "95% occlusion of LAD, stent placement successful",
    date: "Jan 29, 2026 - 4:00 PM",
    provider: "Dr. Williams",
  },
  {
    id: "4",
    type: "medication",
    title: "Medications Prescribed",
    description: "Aspirin, Plavix, Atorvastatin, Metoprolol",
    date: "Jan 29, 2026 - 6:00 PM",
  },
  {
    id: "5",
    type: "lab",
    title: "Lab Results - Troponin",
    description: "Initial: 2.5 ng/mL (elevated), Follow-up: 1.2 ng/mL",
    date: "Jan 29, 2026 - 8:00 PM",
  },
  {
    id: "6",
    type: "note",
    title: "Cardiology Consult Note",
    description: "Patient stable post-PCI, continue monitoring",
    date: "Jan 30, 2026 - 8:00 AM",
    provider: "Dr. Chen",
  },
];

export const TimelineCardStory: StoryObj<typeof TimelineCard> = {
  render: () => (
    <div className="max-w-md">
      <TimelineCard events={sampleEvents} />
    </div>
  ),
};

// All cards together
export const AllMedicalCards: StoryObj = {
  render: () => (
    <div className="space-y-8">
      <section>
        <h2 className="text-lg font-semibold mb-4">Patient Cards</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <PatientCard
            id="1"
            firstName="Sarah"
            lastName="Johnson"
            mrn="MRN-2024-001234"
            dateOfBirth="1985-03-15"
            gender="female"
            status="active"
            lastVisit="Jan 28, 2026"
            primaryDiagnosis="Type 2 Diabetes Mellitus"
          />
          <PatientCard
            id="2"
            firstName="James"
            lastName="Wilson"
            mrn="MRN-2024-005678"
            dateOfBirth="1972-08-22"
            gender="male"
            status="critical"
            lastVisit="Jan 29, 2026"
            primaryDiagnosis="Acute Myocardial Infarction"
          />
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Case Cards</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <CaseCard
            id="1"
            patientName="Sarah Johnson"
            caseNumber="2026-0129-001"
            status="open"
            priority="urgent"
            chiefComplaint="Severe chest pain"
            createdAt="Today"
            assignedTo="Dr. Smith"
          />
          <CaseCard
            id="2"
            patientName="Emily Chen"
            caseNumber="2026-0128-015"
            status="pending_review"
            priority="medium"
            chiefComplaint="Follow-up appointment"
            createdAt="Yesterday"
          />
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Diagnosis Cards</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <DiagnosisCard
            id="1"
            condition="Acute Myocardial Infarction"
            icdCode="I21.0"
            confidence={94}
            severity="critical"
            aiGenerated
            createdAt="2 hours ago"
          />
          <DiagnosisCard
            id="2"
            condition="Type 2 Diabetes"
            icdCode="E11.9"
            confidence={87}
            severity="moderate"
            aiGenerated
            verifiedBy="Dr. Chen"
            createdAt="Yesterday"
          />
        </div>
      </section>
    </div>
  ),
};
