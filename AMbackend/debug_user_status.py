"""Debug script to check user status"""

import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User


async def check_users():
    """Check all users and their active status"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("❌ No users found in database")
            return
        
        print(f"\n📊 Found {len(users)} user(s):\n")
        
        for user in users:
            status = "✅ Active" if user.is_active else "❌ Inactive"
            print(f"{status}")
            print(f"  ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Google ID (Firebase UID): {user.google_id}")
            print(f"  Full Name: {user.full_name}")
            print(f"  Role: {user.role}")
            print(f"  is_active: {user.is_active}")
            print(f"  is_superuser: {user.is_superuser}")
            print()


async def activate_all_users():
    """Activate all users"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        updated_count = 0
        for user in users:
            if not user.is_active:
                user.is_active = True
                updated_count += 1
        
        if updated_count > 0:
            await session.commit()
            print(f"✅ Activated {updated_count} user(s)")
        else:
            print("✅ All users are already active")


async def main():
    print("=" * 60)
    print("User Status Debug Tool")
    print("=" * 60)
    
    await check_users()
    
    print("\n" + "=" * 60)
    response = input("Do you want to activate all inactive users? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        await activate_all_users()
        print("\n" + "=" * 60)
        print("Updated User Status:")
        print("=" * 60)
        await check_users()
    else:
        print("No changes made.")


if __name__ == "__main__":
    asyncio.run(main())

