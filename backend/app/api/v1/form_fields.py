import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_profesional, get_db
from app.models.form_field import FormField
from app.models.profesional import Profesional
from app.models.user import User
from app.schemas.form_field import FormFieldCreate, FormFieldOut, FormFieldUpdate

router = APIRouter(tags=["form-fields"])


@router.get("", response_model=list[FormFieldOut])
def list_form_fields(
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = current_user.profesional
    return (
        db.query(FormField)
        .filter(FormField.profesional_id == profesional.id)
        .order_by(FormField.order.asc(), FormField.created_at.asc())
        .all()
    )


@router.post("", response_model=FormFieldOut, status_code=status.HTTP_201_CREATED)
def create_form_field(
    payload: FormFieldCreate,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = current_user.profesional
    field = FormField(
        profesional_id=profesional.id,
        field_name=payload.field_name,
        is_required=payload.is_required,
        order=payload.order,
        field_type=payload.field_type,
        options=payload.options if payload.field_type == "select" else None,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.patch("/{field_id}", response_model=FormFieldOut)
def update_form_field(
    field_id: uuid.UUID,
    payload: FormFieldUpdate,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = current_user.profesional
    field = db.query(FormField).filter(
        FormField.id == field_id,
        FormField.profesional_id == profesional.id,
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(field, key, value)

    # Clear options when type is no longer "select"
    new_type = data.get("field_type", field.field_type)
    if new_type != "select":
        field.options = None

    db.commit()
    db.refresh(field)
    return field


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_form_field(
    field_id: uuid.UUID,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = current_user.profesional
    field = db.query(FormField).filter(
        FormField.id == field_id,
        FormField.profesional_id == profesional.id,
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")

    db.delete(field)
    db.commit()


@router.get("/public/{profesional_link}", response_model=list[FormFieldOut])
def get_public_form_fields(
    profesional_link: str,
    db: Session = Depends(get_db),
):
    """Devuelve los campos del formulario de un profesional para el flujo de reserva. No requiere autenticación."""
    profesional = db.query(Profesional).filter(
        Profesional.public_link == profesional_link
    ).first()
    if not profesional:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")

    return (
        db.query(FormField)
        .filter(FormField.profesional_id == profesional.id)
        .order_by(FormField.order.asc(), FormField.created_at.asc())
        .all()
    )
