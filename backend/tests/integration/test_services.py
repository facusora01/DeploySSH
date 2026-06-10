import uuid
from unittest.mock import MagicMock

import pytest

from app.exceptions.domain_exceptions import ServiceForbiddenError, ServiceNotFoundError
from app.models.service import Service
from app.services.services_service import ServiceService


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.__enter__ = lambda s: s
    uow.__exit__ = MagicMock(return_value=False)
    return uow


@pytest.fixture
def service_svc(mock_uow):
    return ServiceService(uow=mock_uow)


def make_service(**kwargs) -> Service:
    defaults = dict(
        id=uuid.uuid4(),
        profesional_id=1,
        name="Consulta General",
        duration_minutes=30,
        price=None,
        description=None,
        max_slots=1,
        is_active=True,
        deposit_active=False,
        deposit_amount=None,
        deposit_required=False,
    )
    defaults.update(kwargs)
    s = MagicMock(spec=Service)
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


class TestCreateService:
    def test_create_service_happy_path(self, service_svc, mock_uow):
        expected = make_service(name="Masaje", duration_minutes=60)
        mock_uow.service_repo.create.return_value = expected

        result = service_svc.create_service(
            profesional_id=1,
            name="Masaje",
            duration_minutes=60,
        )

        mock_uow.service_repo.create.assert_called_once_with(
            profesional_id=1,
            name="Masaje",
            duration_minutes=60,
            price=None,
            description=None,
            max_slots=1,
            deposit_active=False,
            deposit_amount=None,
            deposit_required=False,
        )
        mock_uow.commit.assert_called_once()
        assert result.name == "Masaje"

    def test_create_service_with_all_fields(self, service_svc, mock_uow):
        expected = make_service(
            name="Consulta",
            duration_minutes=45,
            price=5000.0,
            description="Consulta médica general",
            max_slots=3,
        )
        mock_uow.service_repo.create.return_value = expected

        result = service_svc.create_service(
            profesional_id=1,
            name="Consulta",
            duration_minutes=45,
            price=5000.0,
            description="Consulta médica general",
            max_slots=3,
        )

        mock_uow.service_repo.create.assert_called_once_with(
            profesional_id=1,
            name="Consulta",
            duration_minutes=45,
            price=5000.0,
            description="Consulta médica general",
            max_slots=3,
            deposit_active=False,
            deposit_amount=None,
            deposit_required=False,
        )
        assert result.max_slots == 3
        assert result.price == 5000.0

    def test_create_service_default_max_slots_is_one(self, service_svc, mock_uow):
        mock_uow.service_repo.create.return_value = make_service()

        service_svc.create_service(profesional_id=1, name="X", duration_minutes=15)

        _, kwargs = mock_uow.service_repo.create.call_args
        assert kwargs["max_slots"] == 1

    def test_create_service_price_is_optional(self, service_svc, mock_uow):
        mock_uow.service_repo.create.return_value = make_service(price=None)

        service_svc.create_service(profesional_id=1, name="X", duration_minutes=15)

        _, kwargs = mock_uow.service_repo.create.call_args
        assert kwargs["price"] is None


class TestListServices:
    def test_list_services_returns_active_services(self, service_svc, mock_uow):
        services = [make_service(name="A"), make_service(name="B")]
        mock_uow.service_repo.get_by_professional.return_value = services

        result = service_svc.list_services(profesional_id=1)

        mock_uow.service_repo.get_by_professional.assert_called_once_with(1)
        assert len(result) == 2

    def test_list_services_empty(self, service_svc, mock_uow):
        mock_uow.service_repo.get_by_professional.return_value = []

        result = service_svc.list_services(profesional_id=1)

        assert result == []


class TestUpdateService:
    def test_update_service_happy_path(self, service_svc, mock_uow):
        service_id = uuid.uuid4()
        existing = make_service(id=service_id, profesional_id=1, name="Viejo")
        mock_uow.service_repo.get_by_id.return_value = existing
        mock_uow.service_repo.update.return_value = existing

        service_svc.update_service(
            service_id=service_id,
            profesional_id=1,
            name="Nuevo",
        )

        mock_uow.service_repo.update.assert_called_once_with(existing, name="Nuevo")
        mock_uow.commit.assert_called_once()

    def test_update_service_not_found_unhappy_path(self, service_svc, mock_uow):
        mock_uow.service_repo.get_by_id.return_value = None

        with pytest.raises(ServiceNotFoundError):
            service_svc.update_service(
                service_id=uuid.uuid4(),
                profesional_id=1,
                name="Nuevo",
            )

        mock_uow.commit.assert_not_called()

    def test_update_service_wrong_owner_unhappy_path(self, service_svc, mock_uow):
        service_id = uuid.uuid4()
        existing = make_service(id=service_id, profesional_id=99)
        mock_uow.service_repo.get_by_id.return_value = existing

        with pytest.raises(ServiceForbiddenError):
            service_svc.update_service(
                service_id=service_id,
                profesional_id=1,
                name="Nuevo",
            )

        mock_uow.commit.assert_not_called()


class TestDeleteService:
    def test_delete_service_happy_path(self, service_svc, mock_uow):
        service_id = uuid.uuid4()
        existing = make_service(id=service_id, profesional_id=1)
        mock_uow.service_repo.get_by_id.return_value = existing
        mock_uow.appointment_repo.count_future_appointments.return_value = 0

        service_svc.delete_service(service_id=service_id, profesional_id=1)

        mock_uow.service_repo.soft_delete.assert_called_once_with(existing)
        mock_uow.commit.assert_called_once()

    def test_delete_service_not_found_unhappy_path(self, service_svc, mock_uow):
        mock_uow.service_repo.get_by_id.return_value = None

        with pytest.raises(ServiceNotFoundError):
            service_svc.delete_service(
                service_id=uuid.uuid4(), profesional_id=1
            )

        mock_uow.service_repo.soft_delete.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_delete_service_wrong_owner_unhappy_path(self, service_svc, mock_uow):
        service_id = uuid.uuid4()
        existing = make_service(id=service_id, profesional_id=99)
        mock_uow.service_repo.get_by_id.return_value = existing

        with pytest.raises(ServiceForbiddenError):
            service_svc.delete_service(service_id=service_id, profesional_id=1)

        mock_uow.service_repo.soft_delete.assert_not_called()
        mock_uow.commit.assert_not_called()

    def test_delete_sets_is_active_false(self, service_svc, mock_uow):
        """Verifica que soft_delete marca is_active=False y no borra el registro."""
        service_id = uuid.uuid4()
        existing = make_service(id=service_id, profesional_id=1, is_active=True)
        mock_uow.service_repo.get_by_id.return_value = existing
        mock_uow.appointment_repo.count_future_appointments.return_value = 0

        def do_soft_delete(s):
            s.is_active = False

        mock_uow.service_repo.soft_delete.side_effect = do_soft_delete

        service_svc.delete_service(service_id=service_id, profesional_id=1)

        assert existing.is_active is False