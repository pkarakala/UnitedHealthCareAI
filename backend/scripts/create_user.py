"""
Create a user from the command line (bootstrap for the first admin).

Usage:
    python scripts/create_user.py EMAIL PASSWORD [--role admin] [--name "Full Name"]
"""
import argparse
import asyncio
import sys
import uuid

sys.path.insert(0, ".")

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.security import hash_password


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("--role", default="admin", choices=["admin", "pharmacist", "technician", "readonly"])
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        existing = (
            await db.execute(select(User).where(User.email == args.email.lower()))
        ).scalar_one_or_none()
        if existing:
            print(f"User {args.email} already exists (role={existing.role})")
            return

        user = User(
            id=str(uuid.uuid4()),
            email=args.email.lower(),
            hashed_password=hash_password(args.password),
            full_name=args.name,
            role=args.role,
        )
        db.add(user)
        await db.commit()
        print(f"Created {args.role} user {args.email} (id={user.id})")


if __name__ == "__main__":
    asyncio.run(main())
