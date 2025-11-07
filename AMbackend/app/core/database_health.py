"""Database health check utilities"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


async def check_database_connection() -> bool:
    """
    Check if database connection is healthy

    Returns:
        True if database is accessible, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to check connection
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


async def get_database_info() -> dict:
    """
    Get database information

    Returns:
        Dictionary with database info
    """
    try:
        async with AsyncSessionLocal() as session:
            # Get database version
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()

            # Get current database name
            result = await session.execute(text("SELECT current_database()"))
            db_name = result.scalar()

            # Check TimescaleDB extension
            result = await session.execute(
                text(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')"
                )
            )
            has_timescaledb = result.scalar()

            return {
                "connected": True,
                "database": db_name,
                "version": version,
                "timescaledb_enabled": has_timescaledb,
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }
