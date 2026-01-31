"""
NEURAXIS - RxNorm API Client
Service for normalizing drug names and retrieving RxCUI codes.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class RxNormClient:
    """
    Client for the NLM RxNorm API.
    Provides drug concept resolution and property retrieval.
    """

    BASE_URL = "https://rxnav.nlm.nih.gov/REST"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self._cache: Dict[str, str] = {}  # Simple in-memory cache for name -> rxcui

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        Get RxCUI (RxNorm Concept Unique Identifier) for a drug name.
        Uses approximate matching to handle typos.
        """
        if drug_name.lower() in self._cache:
            return self._cache[drug_name.lower()]

        try:
            # First try exact/approximate match
            response = await self.client.get(
                f"{self.BASE_URL}/approximateTerm.json", params={"term": drug_name, "maxEntries": 1}
            )
            response.raise_for_status()
            data = response.json()

            candidate = data.get("approximateGroup", {}).get("candidate")
            if candidate and len(candidate) > 0:
                rxcui = candidate[0].get("rxcui")
                if rxcui:
                    self._cache[drug_name.lower()] = rxcui
                    return rxcui

            return None

        except httpx.HTTPError as e:
            logger.error(f"RxNorm API error for {drug_name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error resolving {drug_name}: {str(e)}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_drug_properties(self, rxcui: str) -> Dict[str, Any]:
        """
        Get properties for a given RxCUI (name, tty, etc.)
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/rxcui/{rxcui}/properties.json")
            response.raise_for_status()
            data = response.json()
            return data.get("properties", {})
        except Exception as e:
            logger.error(f"Error fetching properties for RxCUI {rxcui}: {str(e)}")
            return {}

    async def get_interaction_partners(self, rxcui: str) -> List[Dict[str, Any]]:
        """
        Get known interaction partners from RxNav (Interaction API).
        Note: This hits the NLM Interaction API which uses DrugBank/ONCHigh.
        """
        INTERACTION_URL = "https://rxnav.nlm.nih.gov/REST/interaction/interaction.json"
        try:
            response = await self.client.get(INTERACTION_URL, params={"rxcui": rxcui})
            response.raise_for_status()
            data = response.json()

            interactions = []
            interaction_type_group = data.get("interactionTypeGroup", [])

            for group in interaction_type_group:
                for int_type in group.get("interactionType", []):
                    for pair in int_type.get("interactionPair", []):
                        interactions.append(
                            {
                                "description": pair.get("description"),
                                "severity": pair.get("severity", "N/A"),
                                "interaction_concept": pair.get("interactionConcept", []),
                            }
                        )
            return interactions

        except Exception as e:
            logger.error(f"Error fetching interactions for RxCUI {rxcui}: {str(e)}")
            return []

    async def close(self):
        await self.client.aclose()


# Singleton instance
_rxnorm_client: Optional[RxNormClient] = None


def get_rxnorm_client() -> RxNormClient:
    global _rxnorm_client
    if _rxnorm_client is None:
        _rxnorm_client = RxNormClient()
    return _rxnorm_client
