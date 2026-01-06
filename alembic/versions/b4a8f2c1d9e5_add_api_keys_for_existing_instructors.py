"""Add auto-generated API keys for existing instructors

Revision ID: b4a8f2c1d9e5
Revises: a231cae3ad10
Create Date: 2025-01-05 16:45:00.000000

This migration generates one API key for each instructor that doesn't already have one.
Excludes placeholder instructors (with usernames starting with "instructor_").
"""
from typing import Sequence, Union
from datetime import datetime
import secrets

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4a8f2c1d9e5'
down_revision: Union[str, None] = 'a231cae3ad10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def generate_api_key() -> str:
    """Generate an API key in the format rmh_<random_base64_string>."""
    random_part = secrets.token_urlsafe(32)
    return f"rmh_{random_part}"


def upgrade() -> None:
    """
    Generate API keys for existing instructors without keys.

    - Finds all instructors
    - Excludes those with placeholder usernames (start with "instructor_")
    - Excludes those who already have API keys
    - Generates one "Primary API Key" per instructor
    """
    conn = op.get_bind()

    # Get all instructors that don't have API keys, excluding placeholders
    query = """
    SELECT i.id
    FROM instructors i
    LEFT JOIN api_keys k ON i.id = k.instructor_id
    WHERE k.id IS NULL
    AND i.username NOT LIKE 'instructor_%'
    GROUP BY i.id
    """

    result = conn.execute(sa.text(query))
    instructor_ids = [row[0] for row in result]

    if instructor_ids:
        # Generate and insert API keys
        now = datetime.utcnow().isoformat()

        for instructor_id in instructor_ids:
            api_key = generate_api_key()

            insert_query = """
            INSERT INTO api_keys (instructor_id, key, name, is_active, created_at)
            VALUES (:instructor_id, :key, :name, :is_active, :created_at)
            """

            conn.execute(
                sa.text(insert_query),
                {
                    'instructor_id': instructor_id,
                    'key': api_key,
                    'name': 'Primary API Key',
                    'is_active': True,
                    'created_at': now
                }
            )

        conn.commit()
        print(f"✓ Generated API keys for {len(instructor_ids)} instructor(s)")
    else:
        print("✓ All instructors already have API keys")


def downgrade() -> None:
    """
    Remove API keys that were created by this migration.

    Removes all "Primary API Key" entries that were auto-generated.
    """
    conn = op.get_bind()

    # Delete API keys with the "Primary API Key" name (migration marker)
    # Only delete if they were created after this migration started
    delete_query = """
    DELETE FROM api_keys
    WHERE name = 'Primary API Key'
    AND created_at >= DATETIME('2025-01-05')
    """

    result = conn.execute(sa.text(delete_query))
    conn.commit()

    if result.rowcount:
        print(f"✓ Removed {result.rowcount} auto-generated API key(s)")
    else:
        print("✓ No auto-generated API keys to remove")
