#!/usr/bin/env python3
"""
Seed demo data — Creates a sample case with comparables for testing.

Usage:
    python infra/scripts/seed-demo.py

Requires the backend to be importable (run from project root).
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# Fixed UUIDs for reproducibility
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_CASE_ID = uuid.UUID("00000000-0000-0000-0000-000000000100")
DEMO_SOURCE_IDS = [
    uuid.UUID("00000000-0000-0000-0000-000000000201"),
    uuid.UUID("00000000-0000-0000-0000-000000000202"),
    uuid.UUID("00000000-0000-0000-0000-000000000203"),
]
DEMO_COMP_IDS = [
    uuid.UUID("00000000-0000-0000-0000-000000000301"),
    uuid.UUID("00000000-0000-0000-0000-000000000302"),
    uuid.UUID("00000000-0000-0000-0000-000000000303"),
]


SAMPLE_COMPS = [
    {
        "property_title": "Villa in Al Nakheel — 5BR Modern",
        "city": "Riyadh",
        "district": "Al Nakheel",
        "property_type": "villa",
        "evidence_type": "listing_asking",
        "asking_price": 3_500_000,
        "primary_area_sqm": 450,
        "price_per_sqm": 7777.78,
        "listing_date": "2025-12-10",
        "tenure": "freehold",
        "latitude": 24.7573,
        "longitude": 46.6401,
        "url": "https://aqar.fm/listing/demo-villa-nakheel",
    },
    {
        "property_title": "Apartment in Olaya — 3BR Tower Unit",
        "city": "Riyadh",
        "district": "Olaya",
        "property_type": "apartment",
        "evidence_type": "listing_asking",
        "asking_price": 1_850_000,
        "primary_area_sqm": 185,
        "price_per_sqm": 10000.00,
        "listing_date": "2026-01-20",
        "tenure": "freehold",
        "latitude": 24.6905,
        "longitude": 46.6856,
        "url": "https://aqar.fm/listing/demo-apt-olaya",
    },
    {
        "property_title": "Land in Al Malqa — Commercial Plot",
        "city": "Riyadh",
        "district": "Al Malqa",
        "property_type": "land",
        "evidence_type": "transaction_achieved",
        "transacted_price": 5_200_000,
        "primary_area_sqm": 800,
        "price_per_sqm": 6500.00,
        "transaction_date": "2025-11-15",
        "latitude": 24.8100,
        "longitude": 46.6250,
        "url": "https://aqarsas.sa/transaction/demo-land-malqa",
    },
]


async def seed():
    from api.app.database import engine, Base, async_session
    import api.app.models as models

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if demo case already exists
        from sqlalchemy import select
        existing = await db.scalar(
            select(models.Case).where(models.Case.id == DEMO_CASE_ID)
        )
        if existing:
            print(f"⚠  Demo case already exists: {existing.title}")
            print("   Delete muqayyim_dev.db and re-run to get a fresh seed.")
            return

        # Create demo case
        case = models.Case(
            id=DEMO_CASE_ID,
            title="Demo — Mixed Property Comparison, Riyadh",
            description="Sample case with 3 demo comparables: villa, apartment, and land in Riyadh districts.",
            status="in_progress",
            created_by=DEMO_USER_ID,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(case)
        print(f"✓  Created case: {case.title}")

        for i, comp_data in enumerate(SAMPLE_COMPS):
            source_id = DEMO_SOURCE_IDS[i]
            comp_id = DEMO_COMP_IDS[i]

            # Create source
            source = models.Source(
                id=source_id,
                case_id=DEMO_CASE_ID,
                source_type="url",
                url=comp_data.pop("url"),
                status="fetched",
                created_at=datetime.utcnow(),
            )
            db.add(source)

            # Create comparable
            comp = models.Comparable(
                id=comp_id,
                case_id=DEMO_CASE_ID,
                source_id=source_id,
                status="active",
                reliability_score=3 if comp_data.get("evidence_type") == "listing_asking" else 4,
                currency="SAR",
                created_at=datetime.utcnow(),
                **comp_data,
            )
            db.add(comp)

            # Create extracted fields for key values
            for field_name in ["asking_price", "primary_area_sqm", "city", "district", "property_type"]:
                val = comp_data.get(field_name) or getattr(comp, field_name, None)
                if val is None:
                    continue
                ef = models.ExtractedField(
                    id=uuid.uuid4(),
                    extraction_job_id=None,
                    comparable_id=comp_id,
                    field_name=field_name,
                    raw_value=str(val),
                    normalized_value=str(val),
                    display_value=str(val),
                    confidence=0.85,
                    classification="fact",
                    citation={
                        "source_type": "url",
                        "source_url_or_name": source.url,
                        "extractor_name": "seed-demo",
                        "extractor_version": "1.0.0",
                        "parse_confidence": 0.85,
                        "snippet": f"Demo data for {field_name}",
                    },
                    extraction_version="1.0.0",
                    extracted_at=datetime.utcnow(),
                )
                db.add(ef)

            print(f"   ✓  Comparable {i+1}: {comp.property_title} ({comp.district})")

        # Create audit log entry
        audit = models.AuditLog(
            id=uuid.uuid4(),
            entity_type="case",
            entity_id=DEMO_CASE_ID,
            action="seeded",
            user_id=DEMO_USER_ID,
            details={"method": "seed-demo.py", "comps_created": len(SAMPLE_COMPS)},
            timestamp=datetime.utcnow(),
        )
        db.add(audit)

        await db.commit()
        print(f"\n✅ Demo data seeded successfully!")
        print(f"   Case: {case.title}")
        print(f"   Comparables: {len(SAMPLE_COMPS)}")
        print(f"   Open http://localhost:3000 to see the data")


if __name__ == "__main__":
    print("🌱 Seeding Muqayyim demo data...\n")
    asyncio.run(seed())
