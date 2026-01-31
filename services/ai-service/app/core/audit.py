import json
import logging
from datetime import datetime
from typing import Dict, Optional

# Create dedicated logger
logger = logging.getLogger("audit")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False  # Don't duplicate in root logger if simple config already


class AuditLogger:
    """
    HIPAA Compliant Audit Logging.
    Tracks 'Who, What, When, Where, Why' for every PHI access.
    """

    @staticmethod
    def log_access(
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        access_granted: bool = True,
        ip_address: str = "unknown",
        details: Optional[Dict] = None,
    ):
        entry = {
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_class": "PHI_ACCESS",
            "actor": {"user_id": user_id, "ip_address": ip_address},
            "action": {
                "type": action,  # e.g. VIEW, MODIFY, EXPORT
                "granted": access_granted,
            },
            "resource": {"type": resource_type, "id": resource_id},
            "meta": details or {},
        }

        # Serialize to JSON Line
        logger.info(json.dumps(entry))


audit = AuditLogger()
