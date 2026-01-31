/**
 * NEURAXIS - Image Upload Step
 * Drag-drop multiple file upload with preview
 */

"use client";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCaseForm } from "@/contexts/CaseFormContext";
import { cn } from "@/lib/utils";
import type { CaseImage } from "@/types/medical-case";
import React, { useCallback, useRef, useState } from "react";

const IMAGE_TYPES = [
  { value: "photo", label: "Photo" },
  { value: "xray", label: "X-Ray" },
  { value: "scan", label: "CT/MRI Scan" },
  { value: "document", label: "Document" },
  { value: "other", label: "Other" },
];

const ACCEPTED_TYPES = "image/*,.pdf,.doc,.docx,.dicom,.dcm";

export function ImageUploadStep() {
  const { state, addImage, updateImage, removeImage, nextStep, prevStep } =
    useCaseForm();
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      handleFiles(files);
    },
    [addImage]
  );

  const handleFiles = (files: File[]) => {
    files.forEach((file) => {
      // Create preview URL
      const url = URL.createObjectURL(file);
      const isImage = file.type.startsWith("image/");

      addImage({
        file,
        url: isImage ? url : undefined,
        thumbnailUrl: isImage ? url : undefined,
        type: guessImageType(file.name),
        description: "",
        status: "pending",
      });
    });
  };

  const guessImageType = (filename: string): CaseImage["type"] => {
    const lower = filename.toLowerCase();
    if (lower.includes("xray") || lower.includes("x-ray")) return "xray";
    if (lower.includes("ct") || lower.includes("mri") || lower.includes("scan"))
      return "scan";
    if (lower.endsWith(".pdf") || lower.endsWith(".doc")) return "document";
    return "photo";
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async (image: CaseImage & { id: string }) => {
    if (!image.file) return;

    updateImage(image.id, { status: "uploading", uploadProgress: 0 });

    try {
      const formData = new FormData();
      formData.append("file", image.file);
      formData.append("type", image.type);
      formData.append("description", image.description || "");

      const response = await fetch("/api/cases/images/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed");

      const data = await response.json();
      updateImage(image.id, {
        url: data.url,
        thumbnailUrl: data.thumbnailUrl,
        status: "uploaded",
        uploadProgress: 100,
      });
    } catch (error) {
      console.error("Upload error:", error);
      updateImage(image.id, { status: "error" });
    }
  };

  const uploadAllPending = async () => {
    const pending = state.images.filter((img) => img.status === "pending");
    await Promise.all(pending.map(handleUpload));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Upload Images</h2>
        <p className="text-sm text-muted-foreground">
          Add relevant medical images, X-rays, or documents
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/30 hover:border-primary/50"
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_TYPES}
          onChange={handleFileInput}
          className="hidden"
        />

        <svg
          className={cn(
            "h-12 w-12 mx-auto mb-4",
            isDragging ? "text-primary" : "text-muted-foreground"
          )}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>

        <p className="text-lg font-medium mb-1">
          {isDragging ? "Drop files here" : "Drag & drop files"}
        </p>
        <p className="text-sm text-muted-foreground mb-3">or click to browse</p>
        <p className="text-xs text-muted-foreground">
          Supports: Images, PDFs, DICOM files
        </p>
      </div>

      {/* Uploaded files */}
      {state.images.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">
              Uploaded Files ({state.images.length})
            </h3>
            {state.images.some((img) => img.status === "pending") && (
              <Button size="sm" onClick={uploadAllPending}>
                Upload All
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {state.images.map((image) => (
              <div
                key={image.id}
                className={cn(
                  "p-3 rounded-lg border flex gap-3",
                  image.status === "error" && "border-danger bg-danger/5"
                )}
              >
                {/* Thumbnail */}
                <div className="h-20 w-20 rounded bg-muted flex items-center justify-center overflow-hidden shrink-0">
                  {image.thumbnailUrl ? (
                    <img
                      src={image.thumbnailUrl}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <svg
                      className="h-8 w-8 text-muted-foreground"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  )}
                </div>

                {/* Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <p className="text-sm font-medium truncate">
                      {image.file?.name || "Uploaded file"}
                    </p>
                    <button
                      type="button"
                      onClick={() => removeImage(image.id)}
                      className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-danger shrink-0"
                    >
                      <svg
                        className="h-4 w-4"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>

                  {/* Type selector */}
                  <select
                    value={image.type}
                    onChange={(e) =>
                      updateImage(image.id, {
                        type: e.target.value as CaseImage["type"],
                      })
                    }
                    className="h-8 px-2 text-sm rounded border bg-background mb-2 w-full"
                  >
                    {IMAGE_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>

                  {/* Description */}
                  <Input
                    placeholder="Add description..."
                    value={image.description || ""}
                    onChange={(e) =>
                      updateImage(image.id, { description: e.target.value })
                    }
                    className="h-8 text-sm"
                  />

                  {/* Status indicator */}
                  <div className="flex items-center gap-2 mt-2">
                    {image.status === "pending" && (
                      <>
                        <span className="h-2 w-2 rounded-full bg-warning" />
                        <span className="text-xs text-warning">
                          Pending upload
                        </span>
                        <Button
                          size="xs"
                          variant="outline"
                          onClick={() => handleUpload(image)}
                          className="ml-auto"
                        >
                          Upload
                        </Button>
                      </>
                    )}
                    {image.status === "uploading" && (
                      <>
                        <div className="animate-spin h-3 w-3 border-2 border-primary border-t-transparent rounded-full" />
                        <span className="text-xs text-primary">
                          Uploading {image.uploadProgress}%
                        </span>
                      </>
                    )}
                    {image.status === "uploaded" && (
                      <>
                        <span className="h-2 w-2 rounded-full bg-success" />
                        <span className="text-xs text-success">Uploaded</span>
                      </>
                    )}
                    {image.status === "error" && (
                      <>
                        <span className="h-2 w-2 rounded-full bg-danger" />
                        <span className="text-xs text-danger">Failed</span>
                        <Button
                          size="xs"
                          variant="danger"
                          onClick={() => handleUpload(image)}
                          className="ml-auto"
                        >
                          Retry
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <Button type="button" variant="outline" onClick={prevStep}>
          <svg
            className="h-4 w-4 mr-2"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back
        </Button>
        <div className="flex gap-2">
          <Button type="button" variant="ghost" onClick={nextStep}>
            Skip
          </Button>
          <Button type="button" onClick={nextStep} size="lg">
            Continue
            <svg
              className="h-4 w-4 ml-2"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ImageUploadStep;
