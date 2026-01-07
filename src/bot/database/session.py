from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

DATABASE_URL = os.getenv("DATABASE_URL", "")

def prepare_database_url(url: str) -> str:
    if not url:
        return url
    
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    if 'sslmode' in query_params:
        del query_params['sslmode']
    
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    
    return urlunparse(new_parsed)

ASYNC_DATABASE_URL = prepare_database_url(DATABASE_URL)

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False) if ASYNC_DATABASE_URL else None

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
) if engine else None

async def init_db():
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
