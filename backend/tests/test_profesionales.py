from app.models.profesional import Profesional
from app.models.user import User


def test_profesional_update_phone(db):
    # Crear usuario con teléfono inicial
    user = User(
        email="profesional@test.com",
        password_hash="hashed_password_test",
        full_name="Dr. Test Profesional",
        phone="123456789",
        role="profesional",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear perfil de profesional
    profesional = Profesional(
        user_id=user.id,
        specialty="Medicina General",
        license_number="MP-12345",
        experience_years=10,
        bio="Médico con 10 años de experiencia",
        consultation_fee=5000.00,
        is_verified=True,
    )
    db.add(profesional)
    db.commit()
    db.refresh(profesional)

    # Verificar teléfono inicial
    assert user.phone == "123456789"

    # Actualizar teléfono
    user.phone = "119999999"
    db.commit()
    db.refresh(user)

    # Verificar que el teléfono se actualizó
    assert user.phone == "119999999"


def test_profesional_update_multiple_fields(db):
    # Crear usuario con datos iniciales
    user = User(
        email="profesional2@test.com",
        password_hash="hashed_password_test",
        full_name="Dr. Nombre Original",
        phone="123456789",
        role="profesional",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Crear perfil de profesional con datos iniciales
    profesional = Profesional(
        user_id=user.id,
        specialty="Dermatología",
        license_number="MP-11111",
        experience_years=5,
        bio="Bio original",
        consultation_fee=3000.00,
        is_verified=False,
    )
    db.add(profesional)
    db.commit()
    db.refresh(profesional)

    # Verificar datos iniciales
    assert user.full_name == "Dr. Nombre Original"
    assert user.phone == "123456789"
    assert profesional.specialty == "Dermatología"
    assert profesional.license_number == "MP-11111"
    assert profesional.experience_years == 5
    assert profesional.bio == "Bio original"
    assert profesional.consultation_fee == 3000.00
    assert profesional.is_verified is False

    # Actualizar múltiples campos
    user.full_name = "Dr. Nombre Actualizado"
    user.phone = "119999999"
    profesional.specialty = "Dermatología Estética"
    profesional.license_number = "MP-22222"
    profesional.experience_years = 7
    profesional.bio = "Bio actualizada"
    profesional.consultation_fee = 4500.00
    profesional.is_verified = True
    db.commit()
    db.refresh(user)
    db.refresh(profesional)

    # Verificar que todos los campos se actualizaron
    assert user.full_name == "Dr. Nombre Actualizado"
    assert user.phone == "119999999"
    assert profesional.specialty == "Dermatología Estética"
    assert profesional.license_number == "MP-22222"
    assert profesional.experience_years == 7
    assert profesional.bio == "Bio actualizada"
    assert profesional.consultation_fee == 4500.00
    assert profesional.is_verified is True


def test_public_profile_can_be_accessed_by_public_link(client, db):
    user = User(
        email="publicpro@test.com",
        password_hash="hashed_password_test",
        full_name="Dr. Perfil Publico",
        phone="123456789",
        role="profesional",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profesional = Profesional(
        user_id=user.id,
        specialty="Cardiología",
        license_number="MP-99999",
        experience_years=15,
        bio="Especialista en cardiología.",
        consultation_fee=7000.00,
        is_verified=True,
        public_link="dr-perfil-publico",
    )
    db.add(profesional)
    db.commit()

    response = client.get(f"/api/v1/users/{profesional.public_link}/public")
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Dr. Perfil Publico"
    assert data["specialty"] == "Cardiología"
    assert data["public_link"] == "dr-perfil-publico"
