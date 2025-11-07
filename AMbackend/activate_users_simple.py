#!/usr/bin/env python3
"""Simple script to activate all users"""

import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database URL
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/automoney"

# Create engine
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def activate_users():
    """Activate all inactive users"""
    async with AsyncSessionLocal() as session:
        try:
            # Raw SQL to check users
            result = await session.execute(
                """
                SELECT id, email, is_active, role 
                FROM "user" 
                ORDER BY id
                """
            )
            users = result.fetchall()
            
            if not users:
                print("❌ No users found in database")
                return
            
            print(f"\n📊 Found {len(users)} user(s):\n")
            
            inactive_count = 0
            for user in users:
                user_id, email, is_active, role = user
                status = "✅ Active" if is_active else "❌ Inactive"
                print(f"  {status} - {email} (ID: {user_id}, Role: {role})")
                if not is_active:
                    inactive_count += 1
            
            if inactive_count > 0:
                print(f"\n🔧 Activating {inactive_count} inactive user(s)...")
                
                # Activate all users
                await session.execute(
                    """
                    UPDATE "user" 
                    SET is_active = true 
                    WHERE is_active = false
                    """
                )
                await session.commit()
                
                print("✅ All users activated!\n")
                
                # Verify
                result = await session.execute(
                    """
                    SELECT id, email, is_active, role 
                    FROM "user" 
                    ORDER BY id
                    """
                )
                users = result.fetchall()
                
                print("📊 Updated status:")
                for user in users:
                    user_id, email, is_active, role = user
                    status = "✅ Active" if is_active else "❌ Inactive"
                    print(f"  {status} - {email} (ID: {user_id})")
                
                print("\n🎉 Done! Users are now active.")
                print("👉 Please refresh your browser to see the changes.\n")
            else:
                print("\n✅ All users are already active!\n")
        
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("User Activation Tool")
    print("=" * 60)
    
    asyncio.run(activate_users())

