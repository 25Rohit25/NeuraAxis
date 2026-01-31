import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { FormField, Input, TextArea } from "./Input";

const InputMeta: Meta<typeof Input> = {
  title: "UI/Input",
  component: Input,
  tags: ["autodocs"],
  argTypes: {
    type: {
      control: "select",
      options: ["text", "email", "password", "number", "tel", "search"],
    },
    disabled: { control: "boolean" },
    required: { control: "boolean" },
  },
};

export default InputMeta;
type InputStory = StoryObj<typeof Input>;

export const Default: InputStory = {
  args: {
    placeholder: "Enter text...",
  },
};

export const WithLabel: InputStory = {
  args: {
    label: "Email Address",
    placeholder: "doctor@hospital.com",
    type: "email",
  },
};

export const Required: InputStory = {
  args: {
    label: "Patient Name",
    placeholder: "Enter patient name",
    required: true,
  },
};

export const WithError: InputStory = {
  args: {
    label: "Medical Record Number",
    value: "123",
    error: "MRN must be at least 6 characters",
  },
};

export const WithSuccess: InputStory = {
  args: {
    label: "Email",
    value: "valid@email.com",
    isSuccess: true,
    hint: "Email is available",
  },
};

export const WithHint: InputStory = {
  args: {
    label: "Password",
    type: "password",
    placeholder: "Enter password",
    hint: "Must be at least 12 characters with uppercase, lowercase, and numbers",
  },
};

export const WithLeftIcon: InputStory = {
  args: {
    label: "Search Patients",
    placeholder: "Search by name or MRN...",
    leftIcon: (
      <svg
        className="w-4 h-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    ),
  },
};

export const WithRightIcon: InputStory = {
  args: {
    label: "Password",
    type: "password",
    placeholder: "Enter password",
    rightIcon: (
      <button className="hover:text-foreground">
        <svg
          className="w-4 h-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      </button>
    ),
  },
};

export const Disabled: InputStory = {
  args: {
    label: "Disabled Field",
    value: "Cannot edit",
    disabled: true,
  },
};

// TextArea stories
export const TextAreaDefault: StoryObj<typeof TextArea> = {
  render: () => (
    <TextArea
      label="Clinical Notes"
      placeholder="Enter clinical observations..."
      hint="Be thorough in documenting patient symptoms and observations"
    />
  ),
};

export const TextAreaWithCharacterCount: StoryObj<typeof TextArea> = {
  render: () => {
    const [value, setValue] = useState("");
    return (
      <TextArea
        label="Diagnosis Summary"
        placeholder="Enter diagnosis summary..."
        maxLength={500}
        showCharacterCount
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
    );
  },
};

export const TextAreaWithError: StoryObj<typeof TextArea> = {
  render: () => (
    <TextArea
      label="Required Notes"
      value="Too short"
      error="Notes must be at least 50 characters"
    />
  ),
};

// FormField stories
export const FormFieldExample: StoryObj<typeof FormField> = {
  render: () => (
    <FormField label="Date of Birth" required hint="Format: MM/DD/YYYY">
      <input
        type="date"
        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
    </FormField>
  ),
};
