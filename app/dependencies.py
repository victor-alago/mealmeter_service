from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Configure the sessionmaker to use the async engine
async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Dependency to provide an async session for database operations
async def get_db():
    async with async_session() as session:
        yield session
