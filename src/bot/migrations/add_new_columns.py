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
        
        # Add SUPER_ADMIN to userrole enum
        try:
            await conn.execute(text(
                "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'"
            ))
            print("Added SUPER_ADMIN to userrole enum")
        except Exception as e:
            print(f"SUPER_ADMIN role may already exist: {e}")
        
        # Add availabilitystatus enum if not exists
        try:
            await conn.execute(text(
                "DO $$ BEGIN "
                "CREATE TYPE availabilitystatus AS ENUM ('AVAILABLE', 'BUSY', 'AWAY'); "
                "EXCEPTION WHEN duplicate_object THEN null; "
                "END $$;"
            ))
            print("Created availabilitystatus enum")
        except Exception as e:
            print(f"availabilitystatus enum may already exist: {e}")
        
        # Add availability_status column if not exists
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS availability_status availabilitystatus DEFAULT 'AVAILABLE'"
            ))
            print("Added availability_status column to users table")
        except Exception as e:
            print(f"availability_status column may already exist: {e}")
        
        # Update NULL availability_status to AVAILABLE for existing subcontractors
        try:
            await conn.execute(text(
                "UPDATE users SET availability_status = 'AVAILABLE' WHERE availability_status IS NULL AND role = 'SUBCONTRACTOR'"
            ))
            print("Updated NULL availability_status to AVAILABLE")
        except Exception as e:
            print(f"Error updating availability_status: {e}")
        
        # Add TeamType enum if not exists
        try:
            await conn.execute(text(
                "DO $$ BEGIN "
                "CREATE TYPE teamtype AS ENUM ('northwest', 'southeast'); "
                "EXCEPTION WHEN duplicate_object THEN null; "
                "END $$;"
            ))
            print("Created teamtype enum")
        except Exception as e:
            print(f"teamtype enum may already exist: {e}")
        
        # Add team_type column to teams table
        try:
            await conn.execute(text(
                "ALTER TABLE teams ADD COLUMN IF NOT EXISTS team_type teamtype"
            ))
            print("Added team_type column to teams table")
        except Exception as e:
            print(f"team_type column may already exist: {e}")
        
        # Update existing teams and create if they don't exist
        try:
            # Update by team_type first
            await conn.execute(text(
                "UPDATE teams SET name = 'North/West subcontractors' WHERE team_type = 'northwest'"
            ))
            await conn.execute(text(
                "UPDATE teams SET name = 'South/East subcontractors' WHERE team_type = 'southeast'"
            ))
            # Also update by legacy names (in case team_type is NULL)
            await conn.execute(text(
                "UPDATE teams SET name = 'North/West subcontractors', team_type = 'northwest' WHERE name ILIKE '%northwest%'"
            ))
            await conn.execute(text(
                "UPDATE teams SET name = 'South/East subcontractors', team_type = 'southeast' WHERE name ILIKE '%southeast%'"
            ))
            # Create new teams if they don't exist
            await conn.execute(text(
                "INSERT INTO teams (name, team_type) VALUES ('North/West subcontractors', 'northwest') "
                "ON CONFLICT DO NOTHING"
            ))
            await conn.execute(text(
                "INSERT INTO teams (name, team_type) VALUES ('South/East subcontractors', 'southeast') "
                "ON CONFLICT DO NOTHING"
            ))
            print("Updated/created teams (North/West and South/East)")
        except Exception as e:
            print(f"Error creating default teams: {e}")
        
        # Add is_declined column to quotes table
        try:
            await conn.execute(text(
                "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS is_declined BOOLEAN DEFAULT FALSE"
            ))
            print("Added is_declined column to quotes table")
        except Exception as e:
            print(f"is_declined column may already exist: {e}")
        
        # Add decline_reason column to quotes table
        try:
            await conn.execute(text(
                "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS decline_reason TEXT"
            ))
            print("Added decline_reason column to quotes table")
        except Exception as e:
            print(f"decline_reason column may already exist: {e}")
    
    await engine.dispose()
    print("Migration completed!")

if __name__ == "__main__":
    asyncio.run(run_migration())
