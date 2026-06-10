from sqlalchemy.orm import Session

from app.models.client import Client


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_client(self, user_id: int) -> Client:
        """Creates client empty profile."""
        client = Client(user_id=user_id)
        self.db.add(client)
        return client

    def get_by_user_id(self, user_id: int) -> Client | None:
        return self.db.query(Client).filter(Client.user_id == user_id).first()
