"""Test database connection and table creation."""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from app.db.base import engine, Base
from app.db import models  # noqa: F401

async def main():
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)

    try:
        # اتصال به دیتابیس و ساخت جداول
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tables created successfully!")
        
        # لیست جداول ساخته شده
        print("\nTables in database:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    asyncio.run(main())