import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { Button } from "./Button";
import { ConfirmDialog, Modal } from "./Modal";

const meta: Meta<typeof Modal> = {
  title: "UI/Modal",
  component: Modal,
  tags: ["autodocs"],
  argTypes: {
    size: {
      control: "select",
      options: ["sm", "md", "lg", "xl", "full"],
    },
    showCloseButton: { control: "boolean" },
    closeOnOverlayClick: { control: "boolean" },
    closeOnEscape: { control: "boolean" },
  },
};

export default meta;

export const Default: StoryObj = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Open Modal</Button>
        <Modal
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title="Patient Information"
          description="Review and update patient details"
        >
          <div className="space-y-4">
            <p>This is the modal content. You can put any content here.</p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => setIsOpen(false)}>Save Changes</Button>
            </div>
          </div>
        </Modal>
      </>
    );
  },
};

export const Sizes: StoryObj = {
  render: () => {
    const [openSize, setOpenSize] = useState<string | null>(null);
    const sizes = ["sm", "md", "lg", "xl", "full"] as const;

    return (
      <div className="flex gap-2 flex-wrap">
        {sizes.map((size) => (
          <Button
            key={size}
            variant="outline"
            onClick={() => setOpenSize(size)}
          >
            Open {size}
          </Button>
        ))}
        {sizes.map((size) => (
          <Modal
            key={size}
            isOpen={openSize === size}
            onClose={() => setOpenSize(null)}
            title={`${size.toUpperCase()} Modal`}
            size={size}
          >
            <p>This is a {size} sized modal.</p>
          </Modal>
        ))}
      </div>
    );
  },
};

export const WithForm: StoryObj = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Add New Patient</Button>
        <Modal
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          title="Add New Patient"
          size="lg"
        >
          <form className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  className="w-full h-10 rounded-md border px-3"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  className="w-full h-10 rounded-md border px-3"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                className="w-full h-10 rounded-md border px-3"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Date of Birth
              </label>
              <input
                type="date"
                className="w-full h-10 rounded-md border px-3"
              />
            </div>
            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button
                variant="outline"
                type="button"
                onClick={() => setIsOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit">Add Patient</Button>
            </div>
          </form>
        </Modal>
      </>
    );
  },
};

// Confirm Dialog stories
export const ConfirmDialogDefault: StoryObj = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button variant="danger" onClick={() => setIsOpen(true)}>
          Delete Patient
        </Button>
        <ConfirmDialog
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          onConfirm={() => {
            console.log("Confirmed!");
            setIsOpen(false);
          }}
          title="Delete Patient Record"
          message="Are you sure you want to delete this patient record? This action cannot be undone."
          variant="danger"
          confirmText="Delete"
        />
      </>
    );
  },
};

export const ConfirmDialogWarning: StoryObj = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    return (
      <>
        <Button variant="warning" onClick={() => setIsOpen(true)}>
          Archive Case
        </Button>
        <ConfirmDialog
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          onConfirm={() => setIsOpen(false)}
          title="Archive Medical Case"
          message="This will move the case to the archive. You can restore it later from the archive section."
          variant="warning"
          confirmText="Archive"
        />
      </>
    );
  },
};

export const ConfirmDialogLoading: StoryObj = {
  render: () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const handleConfirm = () => {
      setIsLoading(true);
      setTimeout(() => {
        setIsLoading(false);
        setIsOpen(false);
      }, 2000);
    };

    return (
      <>
        <Button onClick={() => setIsOpen(true)}>Save Changes</Button>
        <ConfirmDialog
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
          onConfirm={handleConfirm}
          title="Save Changes"
          message="Do you want to save your changes to this patient record?"
          variant="primary"
          confirmText="Save"
          isLoading={isLoading}
        />
      </>
    );
  },
};
