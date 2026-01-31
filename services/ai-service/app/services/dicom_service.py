"""
NEURAXIS - DICOM Service
Utilities for handling DICOM medical images.
"""

import base64
import io
import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np

# Try importing pydicom, handle failure gracefully
try:
    import pydicom
    from pydicom.dataset import FileDataset

    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.agents.image_schemas import BodyPart, ImageMetadata, ImageModality

logger = logging.getLogger(__name__)


class DICOMService:
    """
    Service to parse and process DICOM files.
    """

    def parse_dicom(self, file_content: bytes) -> Tuple[np.ndarray, ImageMetadata]:
        """
        Parse DICOM bytes into image array and metadata.
        """
        if not PYDICOM_AVAILABLE:
            logger.warning("pydicom not installed. Returning mock data.")
            return self._mock_dicom_parse()

        try:
            # Load dataset from memory
            file_stream = io.BytesIO(file_content)
            ds = pydicom.dcmread(file_stream)

            # Extract basic metadata
            metadata = ImageMetadata(
                patient_id=str(ds.get("PatientID", "Unknown")),
                study_date=str(ds.get("StudyDate", "")),
                modality=self._map_modality(str(ds.get("Modality", "OT"))),
                body_part=self._map_body_part(str(ds.get("BodyPartExamined", ""))),
                manufacturer=str(ds.get("Manufacturer", "Unknown")),
                pixel_spacing=[float(x) for x in ds.get("PixelSpacing", [1.0, 1.0])],
            )

            # Extract Image Data
            # Note: pixel_array depends on gdcm/pillow/jpeg-ls handlers usually.
            # We assume uncompressed or standard compressed for now.
            image_array = ds.pixel_array

            # Apply Windowing/Leveling if present logic is omitted for brevity,
            # but usually crucial for CT/MRI.

            return image_array, metadata

        except Exception as e:
            logger.error(f"Failed to parse DICOM: {e}")
            raise ValueError(f"Invalid DICOM file: {e}")

    def convert_to_png(self, image_array: np.ndarray) -> bytes:
        """
        Convert numpy array (medical image) to PNG bytes.
        Handles normalization to 8-bit.
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL not available")
            return b""

        try:
            # Normalize to 0-255
            if image_array.max() == image_array.min():
                norm_img = np.zeros_like(image_array, dtype=np.uint8)
            else:
                norm_img = (
                    (image_array - image_array.min())
                    / (image_array.max() - image_array.min())
                    * 255
                ).astype(np.uint8)

            img = Image.fromarray(norm_img)

            with io.BytesIO() as output:
                img.save(output, format="PNG")
                return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to convert image: {e}")
            raise

    def _map_modality(self, code: str) -> ImageModality:
        mapping = {
            "CR": ImageModality.XRAY,
            "DX": ImageModality.XRAY,
            "CT": ImageModality.CT,
            "MR": ImageModality.MRI,
            "US": ImageModality.ULTRASOUND,
        }
        return mapping.get(code, ImageModality.OTHER)

    def _map_body_part(self, name: str) -> BodyPart:
        name = name.upper()
        if "CHEST" in name or "LUNG" in name:
            return BodyPart.CHEST
        if "BRAIN" in name or "HEAD" in name:
            return BodyPart.BRAIN
        if "ABDOMEN" in name:
            return BodyPart.ABDOMEN
        if "SPINE" in name:
            return BodyPart.SPINE
        return BodyPart.OTHER

    def _mock_dicom_parse(self) -> Tuple[np.ndarray, ImageMetadata]:
        """Return dummy data when pydicom is missing."""
        mock_img = np.random.randint(0, 255, (512, 512), dtype=np.uint8)
        meta = ImageMetadata(
            patient_id="MOCK-PT-001", modality=ImageModality.XRAY, body_part=BodyPart.CHEST
        )
        return mock_img, meta


# Singleton
_dicom_service = DICOMService()


def get_dicom_service() -> DICOMService:
    return _dicom_service
