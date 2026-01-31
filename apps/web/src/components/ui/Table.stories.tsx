import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { SkeletonTable, Table, type Column } from "./Table";

interface Patient {
  id: string;
  name: string;
  mrn: string;
  age: number;
  gender: string;
  diagnosis: string;
  status: "active" | "discharged" | "critical";
  lastVisit: string;
}

const sampleData: Patient[] = [
  {
    id: "1",
    name: "Sarah Johnson",
    mrn: "MRN-001234",
    age: 39,
    gender: "F",
    diagnosis: "Type 2 Diabetes",
    status: "active",
    lastVisit: "2026-01-28",
  },
  {
    id: "2",
    name: "James Wilson",
    mrn: "MRN-005678",
    age: 53,
    gender: "M",
    diagnosis: "Hypertension",
    status: "critical",
    lastVisit: "2026-01-29",
  },
  {
    id: "3",
    name: "Emily Chen",
    mrn: "MRN-009012",
    age: 35,
    gender: "F",
    diagnosis: "Appendectomy Recovery",
    status: "discharged",
    lastVisit: "2026-01-20",
  },
  {
    id: "4",
    name: "Michael Brown",
    mrn: "MRN-003456",
    age: 57,
    gender: "M",
    diagnosis: "Coronary Artery Disease",
    status: "active",
    lastVisit: "2026-01-25",
  },
  {
    id: "5",
    name: "Lisa Martinez",
    mrn: "MRN-007890",
    age: 42,
    gender: "F",
    diagnosis: "Rheumatoid Arthritis",
    status: "active",
    lastVisit: "2026-01-22",
  },
];

const columns: Column<Patient>[] = [
  { key: "name", header: "Patient Name", sortable: true },
  { key: "mrn", header: "MRN", sortable: true },
  { key: "age", header: "Age", sortable: true, align: "center" },
  { key: "gender", header: "Gender", align: "center" },
  { key: "diagnosis", header: "Primary Diagnosis", sortable: true },
  {
    key: "status",
    header: "Status",
    align: "center",
    render: (value: string) => {
      const colors = {
        active: "bg-success/10 text-success",
        discharged: "bg-secondary/20 text-secondary-foreground",
        critical: "bg-danger/10 text-danger",
      };
      return (
        <span
          className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${colors[value as keyof typeof colors]}`}
        >
          {value}
        </span>
      );
    },
  },
  { key: "lastVisit", header: "Last Visit", sortable: true },
];

const meta: Meta<typeof Table> = {
  title: "UI/Table",
  component: Table,
  tags: ["autodocs"],
  parameters: {
    docs: {
      description: {
        component:
          "A data table with sorting, selection, and pagination support.",
      },
    },
  },
};

export default meta;

export const Default: StoryObj = {
  render: () => <Table columns={columns} data={sampleData} keyField="id" />,
};

export const Sortable: StoryObj = {
  render: () => {
    const [sortColumn, setSortColumn] = useState<string>("");
    const [sortDirection, setSortDirection] = useState<"asc" | "desc" | null>(
      null
    );

    const sortedData = [...sampleData].sort((a, b) => {
      if (!sortColumn || !sortDirection) return 0;
      const aVal = a[sortColumn as keyof Patient];
      const bVal = b[sortColumn as keyof Patient];
      if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return (
      <Table
        columns={columns}
        data={sortedData}
        keyField="id"
        sortable
        sortColumn={sortColumn}
        sortDirection={sortDirection}
        onSort={(col, dir) => {
          setSortColumn(col);
          setSortDirection(dir);
        }}
      />
    );
  },
};

export const Selectable: StoryObj = {
  render: () => {
    const [selected, setSelected] = useState<Set<string>>(new Set());

    return (
      <div className="space-y-4">
        <div className="text-sm text-muted-foreground">
          Selected:{" "}
          {selected.size === 0 ? "None" : Array.from(selected).join(", ")}
        </div>
        <Table
          columns={columns}
          data={sampleData}
          keyField="id"
          selectable
          selectedRows={selected}
          onSelectionChange={setSelected}
        />
      </div>
    );
  },
};

export const WithPagination: StoryObj = {
  render: () => {
    const [page, setPage] = useState(1);
    const pageSize = 3;
    const paginatedData = sampleData.slice(
      (page - 1) * pageSize,
      page * pageSize
    );

    return (
      <Table
        columns={columns}
        data={paginatedData}
        keyField="id"
        pagination={{
          currentPage: page,
          totalPages: Math.ceil(sampleData.length / pageSize),
          onPageChange: setPage,
        }}
      />
    );
  },
};

export const ClickableRows: StoryObj = {
  render: () => (
    <Table
      columns={columns}
      data={sampleData}
      keyField="id"
      onRowClick={(row) => alert(`Clicked: ${row.name}`)}
    />
  ),
};

export const Loading: StoryObj = {
  render: () => <Table columns={columns} data={[]} keyField="id" isLoading />,
};

export const Empty: StoryObj = {
  render: () => (
    <Table
      columns={columns}
      data={[]}
      keyField="id"
      emptyMessage="No patients found matching your search criteria"
    />
  ),
};

export const SkeletonTableStory: StoryObj = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-sm font-medium mb-2">5 columns, 5 rows</h3>
        <SkeletonTable columns={5} rows={5} />
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">
          3 columns, 3 rows, no header
        </h3>
        <SkeletonTable columns={3} rows={3} showHeader={false} />
      </div>
    </div>
  ),
};

export const FullFeatured: StoryObj = {
  render: () => {
    const [page, setPage] = useState(1);
    const [sortColumn, setSortColumn] = useState<string>("");
    const [sortDirection, setSortDirection] = useState<"asc" | "desc" | null>(
      null
    );
    const [selected, setSelected] = useState<Set<string>>(new Set());

    const pageSize = 3;

    const sortedData = [...sampleData].sort((a, b) => {
      if (!sortColumn || !sortDirection) return 0;
      const aVal = a[sortColumn as keyof Patient];
      const bVal = b[sortColumn as keyof Patient];
      if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    const paginatedData = sortedData.slice(
      (page - 1) * pageSize,
      page * pageSize
    );

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {selected.size} of {sampleData.length} selected
          </span>
          {selected.size > 0 && (
            <button className="text-sm text-danger hover:underline">
              Delete selected
            </button>
          )}
        </div>
        <Table
          columns={columns}
          data={paginatedData}
          keyField="id"
          sortable
          selectable
          sortColumn={sortColumn}
          sortDirection={sortDirection}
          selectedRows={selected}
          onSort={(col, dir) => {
            setSortColumn(col);
            setSortDirection(dir);
          }}
          onSelectionChange={setSelected}
          onRowClick={(row) => console.log("Clicked:", row)}
          pagination={{
            currentPage: page,
            totalPages: Math.ceil(sampleData.length / pageSize),
            onPageChange: setPage,
          }}
        />
      </div>
    );
  },
};
