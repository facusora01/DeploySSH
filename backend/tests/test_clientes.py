from datetime import date

from app.models.client import Client
from app.models.user import User


def test_cliente_update_phone(db):
    # Crear usuario con teléfono inicial
    user = User(
        email="cliente@test.com",
        password_hash="hashed_password_test",
        full_name="Test Cliente",
        phone="123456789",
        role="cliente",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear perfil de cliente
    cliente = Client(
        user_id=user.id,
        dni="12345678",
        date_of_birth=date(1990, 1, 1),
        address="Calle Test 123",
        city="Buenos Aires",
        notes="Cliente de prueba",
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    # Verificar teléfono inicial
    assert user.phone == "123456789"

    # Actualizar teléfono
    user.phone = "119999999"
    db.commit()
    db.refresh(user)

    # Verificar que el teléfono se actualizó
    assert user.phone == "119999999"


def test_cliente_update_multiple_fields(db):
    # Crear usuario con datos iniciales
    user = User(
        email="cliente2@test.com",
        password_hash="hashed_password_test",
        full_name="Nombre Original",
        phone="123456789",
        role="cliente",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear perfil de cliente con datos iniciales
    cliente = Client(
        user_id=user.id,
        dni="11111111",
        date_of_birth=date(1985, 10, 20),
        address="Dirección Original",
        city="Ciudad Original",
        notes="Notas originales",
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    # Verificar datos iniciales
    assert user.full_name == "Nombre Original"
    assert user.phone == "123456789"
    assert cliente.address == "Dirección Original"
    assert cliente.city == "Ciudad Original"
    assert cliente.notes == "Notas originales"

    # Actualizar múltiples campos
    user.full_name = "Nombre Actualizado"
    user.phone = "119999999"
    cliente.address = "Dirección Actualizada"
    cliente.city = "Ciudad Actualizada"
    cliente.notes = "Notas actualizadas"
    db.commit()
    db.refresh(user)
    db.refresh(cliente)

    # Verificar que todos los campos se actualizaron
    assert user.full_name == "Nombre Actualizado"
    assert user.phone == "119999999"
    assert cliente.address == "Dirección Actualizada"
    assert cliente.city == "Ciudad Actualizada"
    assert cliente.notes == "Notas actualizadas"
