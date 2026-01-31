import type { Meta, StoryObj } from "@storybook/react";
import { Alert } from "./Alert";

const meta: Meta<typeof Alert> = {
  title: "UI/Alert",
  component: Alert,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["info", "success", "warning", "error", "default"],
    },
    closable: { control: "boolean" },
  },
};

export default meta;
type Story = StoryObj<typeof Alert>;

export const Info: Story = {
  args: {
    variant: "info",
    title: "Information",
    children: "This is an informational alert for general notices.",
  },
};

export const Success: Story = {
  args: {
    variant: "success",
    title: "Success",
    children: "The patient record has been saved successfully.",
  },
};

export const Warning: Story = {
  args: {
    variant: "warning",
    title: "Warning",
    children: "Please review the medication interactions before proceeding.",
  },
};

export const Error: Story = {
  args: {
    variant: "error",
    title: "Error",
    children: "Failed to upload the medical image. Please try again.",
  },
};

export const Closable: Story = {
  args: {
    variant: "info",
    title: "Dismissible Alert",
    children: "Click the X button to dismiss this alert.",
    closable: true,
    onClose: () => console.log("Alert closed"),
  },
};

export const WithoutTitle: Story = {
  args: {
    variant: "success",
    children: "Changes saved successfully.",
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="space-y-4">
      <Alert variant="info" title="Information">
        This is an informational alert.
      </Alert>
      <Alert variant="success" title="Success">
        Operation completed successfully.
      </Alert>
      <Alert variant="warning" title="Warning">
        Please review before continuing.
      </Alert>
      <Alert variant="error" title="Error">
        Something went wrong.
      </Alert>
      <Alert variant="default" title="Default">
        A neutral notification.
      </Alert>
    </div>
  ),
};
