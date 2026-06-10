from sqlalchemy.orm import Session

import secrets

def _generate_public_link() -> str:
    return secrets.token_urlsafe(10)

from app.models.profesional import Profesional


class ProfesionalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_profesional(
        self,
        user_id: int,
        specialty: str,
        public_link: str | None = None,
    ) -> Profesional:
        """Creates intial profesional account with speciality and public profile link."""
        if public_link is None:
            public_link = _generate_public_link()
            while self.db.query(Profesional).filter(Profesional.public_link == public_link).first():
                public_link = _generate_public_link()

        profesional = Profesional(
            user_id=user_id,
            specialty=specialty,
            public_link=public_link,
        )
        self.db.add(profesional)
        return profesional

    def get_by_id(self, profesional_id: int) -> Profesional | None:
        return self.db.get(Profesional, profesional_id)

    def update(self, profesional: Profesional, **fields) -> Profesional:
        """Aplica los campos no-None sobre el objeto. SQLAlchemy detecta el dirty."""
        for key, value in fields.items():
            if hasattr(profesional, key):
                setattr(profesional, key, value)
        return profesional