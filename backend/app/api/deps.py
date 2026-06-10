from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.db.unit_of_work import UnitOfWork
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.services_service import ServiceService
from app.services.availability_service import AvailabilityService
from app.services.agenda_service import AgendaService
from app.services.appointment_service import AppointmentService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_cliente(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("client", "cliente"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized as cliente"
        )
    return current_user


async def get_current_profesional(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "profesional":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as profesional",
        )
    return current_user


async def get_current_local(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "local":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized as local"
        )
    return current_user


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    with UnitOfWork(db) as uow:
        yield AuthService(uow)

def get_service_service(db: Session = Depends(get_db)) -> ServiceService:
    with UnitOfWork(db) as uow:
        yield ServiceService(uow)

def get_availability_service(db: Session = Depends(get_db)) -> AvailabilityService:
    with UnitOfWork(db) as uow:
        yield AvailabilityService(uow)

def get_agenda_service(db: Session = Depends(get_db)) -> AgendaService:
    with UnitOfWork(db) as uow:
        yield AgendaService(uow)

def get_appointment_service(db: Session = Depends(get_db)) -> AppointmentService:
    with UnitOfWork(db) as uow:
        yield AppointmentService(uow)