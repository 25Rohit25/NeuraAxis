"""
NEURAXIS - OpenFDA API Client
Service for retrieving FDA drug labels and safety information.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class OpenFDAClient:
    """
    Client for the openFDA API.
    Retrieves drug labels, warnings, and adverse event data.
    """

    BASE_URL = "https://api.fda.gov/drug/label.json"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_drug_label(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a drug label by brand or generic name.
        """
        try:
            # Query by brand_name or generic_name
            # Enclose in quotes for exact phrase matching
            query = f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"'

            response = await self.client.get(self.BASE_URL, params={"search": query, "limit": 1})

            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if results:
                return results[0]
            return None

        except httpx.HTTPError as e:
            logger.warning(f"OpenFDA API error for {drug_name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching label for {drug_name}: {str(e)}")
            return None

    def extract_safety_info(self, label_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key safety sections from the raw label JSON.
        """
        if not label_data:
            return {}

        return {
            "warnings": label_data.get("warnings", []),
            "boxed_warning": label_data.get("boxed_warning", []),
            "contraindications": label_data.get("contraindications", []),
            "interactions": label_data.get("drug_interactions", []),
            "pregnancy": label_data.get("pregnancy", []),
            "nursing_mothers": label_data.get("nursing_mothers", []),
            "pediatric_use": label_data.get("pediatric_use", []),
            "geriatric_use": label_data.get("geriatric_use", []),
        }

    async def close(self):
        await self.client.aclose()


# Singleton instance
_openfda_client: Optional[OpenFDAClient] = None


def get_openfda_client() -> OpenFDAClient:
    global _openfda_client
    if _openfda_client is None:
        _openfda_client = OpenFDAClient()
    return _openfda_client
