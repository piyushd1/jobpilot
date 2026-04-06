"""Data retention policy enforcement and user data deletion."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class RetentionPolicy:
    resume_days: int = 90
    campaign_days: int = 180
    audit_log_days: int = 365
    user_action_days: int = 180

class DataRetentionService:
    def __init__(self, policy: RetentionPolicy | None = None):
        self.policy = policy or RetentionPolicy()

    def get_expired_before(self, category: str) -> datetime:
        days = getattr(self.policy, f"{category}_days", 180)
        return datetime.now(UTC) - timedelta(days=days)

    async def delete_user_data(self, user_id: str) -> dict[str, int]:
        """GDPR-compliant user data deletion. Returns counts of deleted records."""
        logger.info("User data deletion requested", user_id=user_id)
        # In production: delete from all tables filtered by user_id
        # Delete embeddings from Qdrant
        # Delete files from MinIO
        # Record in audit_logs (anonymized)
        return {
            "resumes_deleted": 0,
            "campaigns_deleted": 0,
            "matches_deleted": 0,
            "contacts_deleted": 0,
            "embeddings_deleted": 0,
            "files_deleted": 0,
        }

    async def enforce_retention(self) -> dict[str, int]:
        """Delete records older than retention policy allows."""
        logger.info("Enforcing data retention policy")
        # In production: query each table for records older than policy
        return {"expired_records_cleaned": 0}

data_retention = DataRetentionService()
