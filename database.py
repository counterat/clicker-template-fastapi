from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import DATABASE_URL, DATABASE_URL_SYNC
from contextlib import asynccontextmanager, contextmanager




engine = create_async_engine(DATABASE_URL, echo=False)

sync_engine = create_engine(DATABASE_URL_SYNC)

SyncSession = sessionmaker(bind=sync_engine)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@asynccontextmanager 
async def get_session(transaction = False) -> AsyncSession:
    if not transaction:
        async with async_session() as session:
            yield session
    else:
        async with async_session() as session:
            async with session.begin():
                yield session    
                
@contextmanager
def get_sync_session() -> Session:
    with SyncSession() as session:
        yield session
        
async def create_session() -> AsyncSession:
    async with async_session() as session:
        yield session

        