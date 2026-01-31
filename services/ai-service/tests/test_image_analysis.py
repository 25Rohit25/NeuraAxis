"""
NEURAXIS - Image Analysis Agent Tests
"""

import base64
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.image_analysis import ImageAnalysisAgent, ImageAnalysisRequest, ImageModality
from app.agents.image_schemas import AbnormalityFinding, ImageAnalysisResponse

# =============================================================================
# Test Data
# =============================================================================

# Valid base64 encoded dummy image
DUMMY_IMAGE_B64 = base64.b64encode(b"fake_image_bytes").decode("utf-8")

MOCK_REQUEST = ImageAnalysisRequest(
    case_id="img-case-001", image_data_base64=DUMMY_IMAGE_B64, modality=ImageModality.XRAY
)

# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
class TestImageAnalysisAgent:
    @pytest.fixture
    def agent(self):
        return ImageAnalysisAgent()

    async def test_analyze_image_flow(self, agent):
        """Test full analysis flow with simulated models."""

        # We don't need to patch much because the models are already simulated classes in the file
        # But let's verify the response structure

        response = await agent.analyze_image(MOCK_REQUEST)

        assert isinstance(response, ImageAnalysisResponse)
        assert response.case_id == MOCK_REQUEST.case_id
        assert response.modality == ImageModality.XRAY

        # Check simulated findings
        assert len(response.findings) > 0
        finding = response.findings[0]
        assert finding.type == "Pneumonia"  # From simulated Gemini/ResNet
        assert finding.severity in ["Moderate", "Mild"]

        # Check performance metrics
        assert response.processing_time_ms > 0
        assert response.confidence_score > 0.8

    async def test_dicom_fallback_handling(self, agent):
        """Test that the agent handles invalid DICOM by falling back to standard image processing."""

        # Pass random bytes that are NOT a valid DICOM
        req = ImageAnalysisRequest(
            case_id="fallback-test",
            image_data_base64=base64.b64encode(b"NOT_A_DICOM").decode("utf-8"),
            modality=ImageModality.CT,
        )

        # The agent tries DICOM parse, fails, then treats as raw bytes
        # Then passes to ResNet/Gemini mock

        response = await agent.analyze_image(req)

        # Should succeed using fallback metadata
        assert response.modality == ImageModality.CT
        assert len(response.findings) > 0

    async def test_segmentation_trigger(self, agent):
        """Test that segmentation is triggered when findings exist."""

        response = await agent.analyze_image(MOCK_REQUEST)

        # With findings, we expect masks
        assert len(response.segmentation_masks) > 0
        mask = response.segmentation_masks[0]
        assert mask.label == "Lung Opacity"  # From simulated SAM


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
