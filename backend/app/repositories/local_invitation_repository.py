from datetime import datetime

from sqlalchemy.orm import Session

from app.models.local_invitation import LocalInvitation


class LocalInvitationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, local_id: int, email: str, token_hash: str, expires_at: datetime
    ) -> LocalInvitation:
        invitation = LocalInvitation(
            local_id=local_id,
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            status="pending",
        )
        self.db.add(invitation)
        self.db.flush()
        return invitation

    def get_by_id(self, invitation_id: int) -> LocalInvitation | None:
        return self.db.get(LocalInvitation, invitation_id)

    def get_by_token_hash(self, token_hash: str) -> LocalInvitation | None:
        return (
            self.db.query(LocalInvitation)
            .filter(LocalInvitation.token_hash == token_hash)
            .first()
        )

    def get_by_local_and_email(
        self, local_id: int, email: str
    ) -> LocalInvitation | None:
        return (
            self.db.query(LocalInvitation)
            .filter(
                LocalInvitation.local_id == local_id,
                LocalInvitation.email == email,
            )
            .first()
        )

    def list_by_local(self, local_id: int) -> list[LocalInvitation]:
        return (
            self.db.query(LocalInvitation)
            .filter(LocalInvitation.local_id == local_id)
            .order_by(LocalInvitation.created_at.desc())
            .all()
        )

    def delete(self, invitation: LocalInvitation) -> None:
        self.db.delete(invitation)
