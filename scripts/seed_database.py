#!/usr/bin/env python3
"""Seed MongoDB with baseline SepsisShield users and patients."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db_connection import close_db, get_db, init_db
from app.database.seed import seed_database


async def main() -> None:
    await init_db()
    await seed_database(await get_db())
    await close_db()
    print("Mongo database seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())
