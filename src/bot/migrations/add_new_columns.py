"""
Migration script to add new columns to the database.
Run this once to update the database schema.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run_migration():
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("DATABASE_URL not set")
        return
    
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url)
    
    async with engine.begin() as conn:
        # Add company_name to jobs table
        try:
            await conn.execute(text(
                "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_name VARCHAR(200)"
            ))
            print("Added company_name column to jobs table")
        except Exception as e:
            print(f"company_name column may already exist: {e}")
        
        # Add super_admin_code to users table
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS super_admin_code VARCHAR(100)"
            ))
            print("Added super_admin_code column to users table")
        except Exception as e:
            print(f"super_admin_code column may already exist: {e}")
        
        # Add SUBMITTED status to jobstatus enum
        try:
            await conn.execute(text(
                "ALTER TYPE jobstatus ADD VALUE IF NOT EXISTS 'SUBMITTED'"
            ))
            print("Added SUBMITTED to jobstatus enum")
        except Exception as e:
            print(f"SUBMITTED status may already exist: {e}")
    
    await engine.dispose()
    print("Migration completed!")

if __name__ == "__main__":
    asyncio.run(run_migration())
