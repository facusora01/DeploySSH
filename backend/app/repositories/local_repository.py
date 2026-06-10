import secrets

from sqlalchemy.orm import Session

from app.models.local import Local


def _generate_public_link() -> str:
    return secrets.token_urlsafe(10)


class LocalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_local(self, user_id: int, local_name: str, phone: str | None = None) -> Local:
        """Creates local profile with auto-generated unique public_link."""
        public_link = _generate_public_link()
        while self.db.query(Local).filter(Local.public_link == public_link).first():
            public_link = _generate_public_link()

        local = Local(user_id=user_id, local_name=local_name, phone=phone, public_link=public_link)
        self.db.add(local)
        return local

    def get_by_user_id(self, user_id: int) -> Local | None:
        return self.db.query(Local).filter(Local.user_id == user_id).first()

    def get_by_public_link(self, slug: str) -> Local | None:
        return self.db.query(Local).filter(Local.public_link == slug).first()
