"""
API Key Service - Manages API key generation and lifecycle
"""
from sqlalchemy.orm import Session
from models_v2 import APIKey, Instructor
from logging_config import get_logger, log_database_operation

logger = get_logger(__name__)


class APIKeyService:
    """Service for managing API keys"""

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
                name="Primary API Key",
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
