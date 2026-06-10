import pytest
from unittest.mock import MagicMock
from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service
from app.models.client import Client
from app.models.profesional import Profesional
from app.models.user import User

def test_appointment_properties_all_relations_exist():
    # Arrange
    user_client = MagicMock(spec=User)
    user_client.full_name = "Jane Client"
    user_client.phone = "+54 9 11 1234 5678"

    client = MagicMock(spec=Client)
    client.user = user_client

    user_pro = MagicMock(spec=User)
    user_pro.full_name = "Dr. John Pro"

    profesional = MagicMock(spec=Profesional)
    profesional.user = user_pro
    profesional.public_link = "dr-john-pro"
    profesional.user_id = 42

    service = MagicMock(spec=Service)
    service.name = "Consultation"
    service.profesional = profesional

    appointment = Appointment()
    appointment.__dict__["service"] = service
    appointment.__dict__["client"] = client

    # Act & Assert
    assert appointment.service_name == "Consultation"
    assert appointment.cliente_name == "Jane Client"
    assert appointment.cliente_phone == "+54 9 11 1234 5678"
    assert appointment.profesional_name == "Dr. John Pro"
    assert appointment.profesional_public_link == "dr-john-pro"

def test_appointment_properties_missing_relations():
    # Arrange
    appointment = Appointment()
    appointment.__dict__["service"] = None
    appointment.__dict__["client"] = None

    # Act & Assert
    assert appointment.service_name == ""
    assert appointment.cliente_name == ""
    assert appointment.cliente_phone is None
    assert appointment.profesional_name == ""
    assert appointment.profesional_public_link == ""

def test_appointment_properties_fallback_public_link_to_user_id():
    # Arrange
    user_pro = MagicMock(spec=User)
    user_pro.full_name = "Dr. John Pro"

    profesional = MagicMock(spec=Profesional)
    profesional.user = user_pro
    profesional.public_link = None  # Missing public link
    profesional.user_id = 99

    service = MagicMock(spec=Service)
    service.name = "Therapy"
    service.profesional = profesional

    appointment = Appointment()
    appointment.__dict__["service"] = service
    appointment.__dict__["client"] = None

    # Act & Assert
    assert appointment.profesional_public_link == "99"
