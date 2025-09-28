"""Script to create default users.

This script can be run independently to create default users
in an existing database.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from puntini.database.base import get_session_maker
from puntini.database.init_db import create_default_roles, create_default_users
from puntini.logging import get_logger

logger = get_logger(__name__)


async def create_default_users_script():
    """Create default users in the database."""
    try:
        logger.info("Creating default users...")
        
        # Get session maker
        session_maker = get_session_maker()
        
        # Create default roles and users
        async with session_maker() as session:
            await create_default_roles(session)
            await create_default_users(session)
        
        logger.info("Default users created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create default users: {e}")
        raise


def main():
    """Main function."""
    asyncio.run(create_default_users_script())


if __name__ == "__main__":
    main()
