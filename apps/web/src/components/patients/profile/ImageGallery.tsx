/**
 * NEURAXIS - Image Gallery Component
 * Medical images with thumbnail view and lightbox
 */

"use client";

import { Modal } from "@/components/ui/Modal";
import { cn, formatDate } from "@/lib/utils";
import type { ImagingType, MedicalImage } from "@/types/patient-profile";
import React, { useCallback, useEffect, useState } from "react";

interface ImageGalleryProps {
  images: MedicalImage[];
  onViewImage?: (image: MedicalImage) => void;
  isLoading?: boolean;
  className?: string;
}

const IMAGING_TYPE_LABELS: Record<ImagingType, string> = {
  xray: "X-Ray",
  ct: "CT Scan",
  mri: "MRI",
  ultrasound: "Ultrasound",
  mammogram: "Mammogram",
  pet: "PET Scan",
  other: "Other",
};

const IMAGING_TYPE_ICONS: Record<ImagingType, React.ReactNode> = {
  xray: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  ct: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="2" x2="12" y2="6" />
      <line x1="12" y1="18" x2="12" y2="22" />
    </svg>
  ),
  mri: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <ellipse cx="12" cy="12" rx="10" ry="4" />
      <path d="M2 12v5c0 2.21 4.48 4 10 4s10-1.79 10-4v-5" />
    </svg>
  ),
  ultrasound: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  mammogram: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M8.5 8.5c0 2.5 1.5 4 3.5 4s3.5-1.5 3.5-4" />
    </svg>
  ),
  pet: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2a10 10 0 0 0 0 20" />
      <path d="M12 2a10 10 0 0 1 0 20" />
    </svg>
  ),
  other: (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  ),
};

export function ImageGallery({
  images,
  onViewImage,
  isLoading,
  className,
}: ImageGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<MedicalImage | null>(null);
  const [filterType, setFilterType] = useState<ImagingType | "all">("all");

  const filteredImages =
    filterType === "all"
      ? images
      : images.filter((img) => img.type === filterType);

  // Get unique imaging types for filter
  const availableTypes = [...new Set(images.map((img) => img.type))];

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!selectedImage) return;

      const currentIndex = filteredImages.findIndex(
        (img) => img.id === selectedImage.id
      );

      if (e.key === "ArrowLeft" && currentIndex > 0) {
        setSelectedImage(filteredImages[currentIndex - 1]);
      } else if (
        e.key === "ArrowRight" &&
        currentIndex < filteredImages.length - 1
      ) {
        setSelectedImage(filteredImages[currentIndex + 1]);
      } else if (e.key === "Escape") {
        setSelectedImage(null);
      }
    },
    [selectedImage, filteredImages]
  );

  useEffect(() => {
    if (selectedImage) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [selectedImage, handleKeyDown]);

  if (isLoading) {
    return (
      <div
        className={cn(
          "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3",
          className
        )}
      >
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="aspect-square rounded-lg bg-muted animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Filter tabs */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
        <button
          onClick={() => setFilterType("all")}
          className={cn(
            "px-3 py-1.5 text-xs rounded-full whitespace-nowrap transition-colors",
            filterType === "all"
              ? "bg-primary text-primary-foreground"
              : "hover:bg-muted"
          )}
        >
          All ({images.length})
        </button>
        {availableTypes.map((type) => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full whitespace-nowrap transition-colors",
              filterType === type
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            {IMAGING_TYPE_ICONS[type]}
            {IMAGING_TYPE_LABELS[type]}(
            {images.filter((img) => img.type === type).length})
          </button>
        ))}
      </div>

      {/* Image grid */}
      {filteredImages.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground bg-muted/30 rounded-lg">
          <svg
            className="h-12 w-12 mx-auto mb-3 opacity-50"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
          <p>No medical images available</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {filteredImages.map((image) => (
            <button
              key={image.id}
              onClick={() => setSelectedImage(image)}
              className="group relative aspect-square rounded-lg overflow-hidden bg-muted border hover:ring-2 hover:ring-primary transition-all"
            >
              {/* Thumbnail */}
              <img
                src={image.thumbnailUrl}
                alt={`${IMAGING_TYPE_LABELS[image.type]} - ${image.bodyPart}`}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform"
              />

              {/* Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="absolute bottom-2 left-2 right-2">
                  <p className="text-white text-xs font-medium truncate">
                    {IMAGING_TYPE_LABELS[image.type]} - {image.bodyPart}
                  </p>
                  <p className="text-white/70 text-xs">
                    {formatDate(image.date)}
                  </p>
                </div>
              </div>

              {/* Type badge */}
              <div className="absolute top-2 right-2 p-1.5 rounded-full bg-black/50 text-white">
                {IMAGING_TYPE_ICONS[image.type]}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Lightbox modal */}
      <Modal
        isOpen={!!selectedImage}
        onClose={() => setSelectedImage(null)}
        title=""
        size="xl"
        className="bg-black"
      >
        {selectedImage && (
          <div className="relative">
            {/* Main image */}
            <div className="relative aspect-[4/3] bg-black rounded-lg overflow-hidden">
              <img
                src={selectedImage.fullImageUrl}
                alt={`${IMAGING_TYPE_LABELS[selectedImage.type]} - ${selectedImage.bodyPart}`}
                className="w-full h-full object-contain"
              />

              {/* Navigation arrows */}
              {filteredImages.length > 1 && (
                <>
                  <button
                    onClick={() => {
                      const i = filteredImages.findIndex(
                        (img) => img.id === selectedImage.id
                      );
                      if (i > 0) setSelectedImage(filteredImages[i - 1]);
                    }}
                    className="absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                    disabled={
                      filteredImages.findIndex(
                        (img) => img.id === selectedImage.id
                      ) === 0
                    }
                  >
                    <svg
                      className="h-6 w-6"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <polyline points="15 18 9 12 15 6" />
                    </svg>
                  </button>
                  <button
                    onClick={() => {
                      const i = filteredImages.findIndex(
                        (img) => img.id === selectedImage.id
                      );
                      if (i < filteredImages.length - 1)
                        setSelectedImage(filteredImages[i + 1]);
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                    disabled={
                      filteredImages.findIndex(
                        (img) => img.id === selectedImage.id
                      ) ===
                      filteredImages.length - 1
                    }
                  >
                    <svg
                      className="h-6 w-6"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </button>
                </>
              )}
            </div>

            {/* Image info */}
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">
                    {IMAGING_TYPE_LABELS[selectedImage.type]} -{" "}
                    {selectedImage.bodyPart}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(selectedImage.date)} • Ordered by{" "}
                    {selectedImage.orderedBy.name}
                  </p>
                </div>
                <div className="flex gap-2">
                  {selectedImage.dicomUrl && (
                    <a
                      href={selectedImage.dicomUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 text-sm rounded border hover:bg-muted"
                    >
                      Open DICOM Viewer
                    </a>
                  )}
                </div>
              </div>

              {/* Findings */}
              {selectedImage.findings && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    Findings
                  </p>
                  <p className="text-sm">{selectedImage.findings}</p>
                </div>
              )}

              {/* Impressions */}
              {selectedImage.impressions && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    Impressions
                  </p>
                  <p className="text-sm">{selectedImage.impressions}</p>
                </div>
              )}

              {/* Radiologist notes */}
              {selectedImage.radiologistNotes && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    Radiologist Notes
                  </p>
                  <p className="text-sm">{selectedImage.radiologistNotes}</p>
                </div>
              )}
            </div>

            {/* Image counter */}
            <div className="mt-4 text-center text-sm text-muted-foreground">
              {filteredImages.findIndex((img) => img.id === selectedImage.id) +
                1}{" "}
              of {filteredImages.length}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default ImageGallery;
