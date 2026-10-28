"""Override service — logs all manual field edits."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.database import Comparable, FieldOverride, ExtractedField


class OverrideService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def override_field(
        self,
        comp_id: str,
        field_name: str,
        new_value: str,
        reason: str,
        user: str = "admin",
    ) -> Optional[FieldOverride]:
        # Get comparable
        result = await self.db.execute(
            select(Comparable).where(Comparable.id == comp_id)
        )
        comp = result.scalar_one_or_none()
        if not comp:
            return None

        # Get current value
        old_value = getattr(comp, field_name, None)
        if old_value is None:
            # Check extracted_fields
            ef_result = await self.db.execute(
                select(ExtractedField)
                .where(ExtractedField.comparable_id == comp_id)
                .where(ExtractedField.field_name == field_name)
            )
            ef = ef_result.scalar_one_or_none()
            if ef:
                old_value = ef.normalized_value or ef.raw_value
        else:
            old_value = str(old_value)

        # Update the field on the comparable if it's a direct column
        if hasattr(comp, field_name):
            setattr(comp, field_name, new_value)
            comp.updated_at = datetime.now(timezone.utc)

        # Also update extracted_field if exists
        ef_result = await self.db.execute(
            select(ExtractedField)
            .where(ExtractedField.comparable_id == comp_id)
            .where(ExtractedField.field_name == field_name)
        )
        ef = ef_result.scalar_one_or_none()
        if ef:
            ef.normalized_value = new_value

        # Log override
        override = FieldOverride(
            id=str(uuid.uuid4()),
            comparable_id=comp_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            overridden_by=user,
            overridden_at=datetime.now(timezone.utc),
        )
        self.db.add(override)
        await self.db.flush()
        return override
