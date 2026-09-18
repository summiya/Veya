from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.domain.users.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def get_by_uuid(self, user_uuid: str) -> User | None:
        return self.db.scalar(select(User).where(User.uuid == user_uuid))

    def create(self, *, email: str, password_hash: str) -> User:
        user = User(email=email.lower(), password_hash=password_hash)
        self.db.add(user)
        self.db.flush()
        return user
