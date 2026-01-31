import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import {
  Breadcrumbs,
  PageInfo,
  Pagination,
  TabPanel,
  Tabs,
} from "./Navigation";

// Breadcrumbs
const BreadcrumbsMeta: Meta<typeof Breadcrumbs> = {
  title: "UI/Navigation/Breadcrumbs",
  component: Breadcrumbs,
  tags: ["autodocs"],
};

export default BreadcrumbsMeta;

export const DefaultBreadcrumbs: StoryObj<typeof Breadcrumbs> = {
  args: {
    items: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Patients", href: "/patients" },
      { label: "Sarah Johnson" },
    ],
  },
};

export const WithIcons: StoryObj<typeof Breadcrumbs> = {
  args: {
    items: [
      {
        label: "Home",
        href: "/",
        icon: (
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
            <polyline points="9 22 9 12 15 12 15 22" />
          </svg>
        ),
      },
      { label: "Cases", href: "/cases" },
      { label: "Case #2026-001" },
    ],
  },
};

export const SlashSeparator: StoryObj<typeof Breadcrumbs> = {
  args: {
    separator: "slash",
    items: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Analytics", href: "/analytics" },
      { label: "Monthly Report" },
    ],
  },
};

// Tabs
export const TabsDefault: StoryObj = {
  render: () => {
    const [activeTab, setActiveTab] = useState("overview");
    return (
      <div>
        <Tabs
          tabs={[
            { id: "overview", label: "Overview" },
            { id: "vitals", label: "Vitals" },
            { id: "medications", label: "Medications", badge: 5 },
            { id: "history", label: "History" },
            { id: "notes", label: "Notes", disabled: true },
          ]}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
        <div className="mt-4 p-4 border rounded-lg">
          <TabPanel id="overview" activeTab={activeTab}>
            <h3 className="font-medium">Patient Overview</h3>
            <p className="text-muted-foreground mt-2">
              General patient information and summary.
            </p>
          </TabPanel>
          <TabPanel id="vitals" activeTab={activeTab}>
            <h3 className="font-medium">Vital Signs</h3>
            <p className="text-muted-foreground mt-2">
              Blood pressure, heart rate, temperature, etc.
            </p>
          </TabPanel>
          <TabPanel id="medications" activeTab={activeTab}>
            <h3 className="font-medium">Current Medications</h3>
            <p className="text-muted-foreground mt-2">
              List of prescribed medications.
            </p>
          </TabPanel>
          <TabPanel id="history" activeTab={activeTab}>
            <h3 className="font-medium">Medical History</h3>
            <p className="text-muted-foreground mt-2">
              Past conditions, surgeries, and treatments.
            </p>
          </TabPanel>
        </div>
      </div>
    );
  },
};

export const TabsPills: StoryObj = {
  render: () => {
    const [activeTab, setActiveTab] = useState("all");
    return (
      <Tabs
        variant="pills"
        tabs={[
          { id: "all", label: "All", badge: 128 },
          { id: "active", label: "Active", badge: 45 },
          { id: "critical", label: "Critical", badge: 3 },
          { id: "discharged", label: "Discharged", badge: 80 },
        ]}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
    );
  },
};

export const TabsUnderline: StoryObj = {
  render: () => {
    const [activeTab, setActiveTab] = useState("details");
    return (
      <Tabs
        variant="underline"
        tabs={[
          { id: "details", label: "Details" },
          { id: "diagnosis", label: "Diagnosis" },
          { id: "treatment", label: "Treatment Plan" },
          { id: "followup", label: "Follow-up" },
        ]}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
    );
  },
};

export const TabsWithIcons: StoryObj = {
  render: () => {
    const [activeTab, setActiveTab] = useState("dashboard");
    return (
      <Tabs
        tabs={[
          {
            id: "dashboard",
            label: "Dashboard",
            icon: (
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            ),
          },
          {
            id: "patients",
            label: "Patients",
            icon: (
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
              </svg>
            ),
          },
          {
            id: "analytics",
            label: "Analytics",
            icon: (
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            ),
          },
        ]}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
    );
  },
};

// Pagination
export const PaginationDefault: StoryObj = {
  render: () => {
    const [page, setPage] = useState(1);
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">Current page: {page}</p>
        <Pagination currentPage={page} totalPages={10} onPageChange={setPage} />
      </div>
    );
  },
};

export const PaginationWithEllipsis: StoryObj = {
  render: () => {
    const [page, setPage] = useState(5);
    return (
      <Pagination currentPage={page} totalPages={20} onPageChange={setPage} />
    );
  },
};

export const PageInfoComponent: StoryObj = {
  render: () => {
    const [page, setPage] = useState(1);
    return (
      <PageInfo
        currentPage={page}
        totalPages={10}
        totalItems={97}
        itemsPerPage={10}
        onPageChange={setPage}
      />
    );
  },
};

// All navigation together
export const AllNavigation: StoryObj = {
  render: () => {
    const [activeTab, setActiveTab] = useState("overview");
    const [page, setPage] = useState(1);

    return (
      <div className="space-y-8">
        <section>
          <h2 className="text-lg font-semibold mb-4">Breadcrumbs</h2>
          <Breadcrumbs
            items={[
              { label: "Dashboard", href: "/dashboard" },
              { label: "Patients", href: "/patients" },
              { label: "Sarah Johnson" },
            ]}
          />
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-4">Tabs</h2>
          <Tabs
            tabs={[
              { id: "overview", label: "Overview" },
              { id: "vitals", label: "Vitals" },
              { id: "medications", label: "Medications", badge: 5 },
            ]}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-4">Pagination</h2>
          <PageInfo
            currentPage={page}
            totalPages={10}
            totalItems={97}
            itemsPerPage={10}
            onPageChange={setPage}
          />
        </section>
      </div>
    );
  },
};
