from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def create_user(
        self,
        full_name: str,
        email: str,
        phone: str,
        password_hash: str,
        role: str,
    ) -> User:
        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        return user
