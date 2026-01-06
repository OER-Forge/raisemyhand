"""
API Key Service - Manages API key generation and lifecycle
"""
from sqlalchemy.orm import Session
from models_v2 import APIKey, Instructor
from logging_config import get_logger, log_database_operation, log_security_event
from datetime import datetime

logger = get_logger(__name__)


class APIKeyService:
    """Service for managing API keys"""

    @staticmethod
    def _generate_key_name() -> str:
        """Generate a timestamp-based name for the API key."""
        return f"API Key - Created {datetime.utcnow().strftime('%b %d, %Y')}"

    @staticmethod
    def auto_generate_api_key(instructor: Instructor, db: Session) -> APIKey:
        """
        Automatically generate an API key for a new instructor.

        Args:
            instructor: The Instructor object (must already be persisted to DB)
            db: Database session

        Returns:
            The newly created APIKey object

        Raises:
            Exception: If API key creation fails
        """
        try:
            # Generate a new API key
            api_key = APIKey(
                instructor_id=instructor.id,
                key=APIKey.generate_key(),  # Uses rmh_{token} format
                name=APIKeyService._generate_key_name(),
                is_active=True
            )

            db.add(api_key)
            db.commit()
            db.refresh(api_key)

            log_database_operation(
                logger,
                "CREATE",
                "api_keys",
                api_key.id,
                success=True
            )

            logger.info(f"Auto-generated API key for instructor {instructor.id} ({instructor.username})")

            return api_key

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to auto-generate API key for instructor {instructor.id}: {e}", exc_info=True)
            raise

    @staticmethod
    def regenerate_api_key(
        instructor: Instructor,
        reason: str,
        revoked_by_id: int,
        db: Session
    ) -> APIKey:
        """
        Regenerate an API key for an instructor.

        This will:
        1. Revoke all existing active API keys for the instructor
        2. Generate a new API key

        Args:
            instructor: The Instructor object
            reason: Reason for regeneration (e.g., "Self-regenerated", "Admin regenerated - compromised")
            revoked_by_id: ID of the user who initiated the regeneration
            db: Database session

        Returns:
            The newly created APIKey object

        Raises:
            Exception: If regeneration fails
        """
        try:
            # Revoke all existing active keys
            active_keys = db.query(APIKey).filter(
                APIKey.instructor_id == instructor.id,
                APIKey.is_active == True
            ).all()

            for key in active_keys:
                key.is_active = False
                key.revoked_by = revoked_by_id
                key.revoked_at = datetime.utcnow()
                key.revocation_reason = reason

                log_security_event(
                    logger,
                    "API_KEY_REVOKED",
                    f"API key {key.id} revoked during regeneration for instructor {instructor.username}: {reason}",
                    severity="warning"
                )

            # Generate new API key
            new_key = APIKey(
                instructor_id=instructor.id,
                key=APIKey.generate_key(),
                name=APIKeyService._generate_key_name(),
                is_active=True
            )

            db.add(new_key)
            db.commit()
            db.refresh(new_key)

            log_database_operation(
                logger,
                "CREATE",
                "api_keys",
                new_key.id,
                success=True
            )

            log_security_event(
                logger,
                "API_KEY_REGENERATED",
                f"New API key {new_key.id} generated for instructor {instructor.username}: {reason}",
                severity="info"
            )

            logger.info(f"Regenerated API key for instructor {instructor.id} ({instructor.username}). Revoked {len(active_keys)} old key(s)")

            return new_key

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to regenerate API key for instructor {instructor.id}: {e}", exc_info=True)
            raise
