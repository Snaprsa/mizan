"""
Audit logger — every significant action gets logged.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import AuditLog


async def log_action(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    user_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log an auditable action.

    Args:
        entity_type: "case", "source", "comparable", "extracted_field", etc.
        entity_id: UUID of the entity
        action: "created", "updated", "extracted", "overridden", "exported", etc.
        user_id: Who performed the action
        details: Additional context as JSON
    """
    entry = AuditLog(
        id=uuid.uuid4(),
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=uuid.UUID(user_id) if user_id else None,
        details=details or {},
        timestamp=datetime.utcnow(),
    )
    db.add(entry)
    # Don't commit here — let the caller's transaction handle it
