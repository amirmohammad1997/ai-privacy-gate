import asyncio
from app.db.base import engine, Base
from app.db import models  # noqa: F401 - برای شناسایی همه مدل‌ها

async def drop_tables():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✅ Tables dropped successfully!")

if __name__ == "__main__":
    asyncio.run(drop_tables())