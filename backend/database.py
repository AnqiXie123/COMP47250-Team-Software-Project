import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL is stored as a standard postgresql:// URL in .env
# We convert it to postgresql+asyncpg:// for SQLAlchemy async
_raw_url = os.getenv("DATABASE_URL", "postgresql://localhost/ecocharge")
DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

import ssl as _ssl

def _make_ssl_context():
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    return ctx

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"ssl": _make_ssl_context()} if "supabase.com" in DATABASE_URL or "supabase.co" in DATABASE_URL else {},
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
