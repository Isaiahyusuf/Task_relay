from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

DATABASE_URL = os.getenv("DATABASE_URL", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

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

def get_connect_args() -> dict:
    if ENVIRONMENT == "production":
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return {"ssl": ssl_context}
    return {}

ASYNC_DATABASE_URL = prepare_database_url(DATABASE_URL)

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=get_connect_args()
) if ASYNC_DATABASE_URL else None

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
) if engine else None

async def init_db():
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
