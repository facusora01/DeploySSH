import uuid
from datetime import datetime, timedelta, time
from unittest.mock import MagicMock, patch
import pytest

from app.services.availability_service import AvailabilityService
from app.models.service import Service
from app.models.weekly_schedule import WeeklySchedule
from app.exceptions.domain_exceptions import ServiceNotFoundError

@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.__enter__ = lambda s: s
    uow.__exit__ = MagicMock(return_value=False)
    return uow

@pytest.fixture
def availability_svc(mock_uow):
    return AvailabilityService(uow=mock_uow)

def make_service(max_slots=1):
    s = MagicMock(spec=Service)
    s.id = uuid.uuid4()
    s.name = "Test Service"
    s.duration_minutes = 60
    s.max_slots = max_slots
    s.is_active = True
    s.deposit_active = False
    s.deposit_amount = None
    s.deposit_required = False
    return s

def test_get_availability_service_not_found(availability_svc, mock_uow):
    mock_uow.service_repo.get_by_id.return_value = None
    
    with pytest.raises(ServiceNotFoundError):
        availability_svc.get_service_availability(uuid.uuid4())

def test_get_availability_filters_full_slots(availability_svc, mock_uow):
    service = make_service(max_slots=2)
    mock_uow.service_repo.get_by_id.return_value = service
    
    profesional = MagicMock()
    profesional.id = 1
    profesional.buffer_minutes = 0
    profesional.public_link = "test-profesional"
    service.profesional = profesional

    mock_ws = []
    for d in range(7):
        ws = MagicMock(spec=WeeklySchedule)
        ws.day_of_week = d
        ws.start_time = time(9, 0)
        ws.end_time = time(18, 0)
        mock_ws.append(ws)
    mock_uow.weekly_schedule_repo.get_by_profesional.return_value = mock_ws
    mock_uow.schedule_block_repo.get_blocks_in_range.return_value = []

    test_now = datetime(2026, 5, 20, 10, 30) # Wednesday (weekday 2)
    with patch('app.services.availability_service.datetime') as mock_dt:
        mock_dt.now.return_value = test_now
        mock_dt.combine = datetime.combine
        mock_dt.date = datetime.date

        slot_11 = datetime(2026, 5, 20, 11, 0)
        slot_12 = datetime(2026, 5, 20, 12, 0)

        mock_uow.appointment_repo.get_occupancy_by_service.return_value = [
            (slot_11, 2),
            (slot_12, 1)
        ]

        result = availability_svc.get_service_availability(service.id, days=1)

        times = [slot.start_time for slot in result.availability]
        assert slot_11 in times
        assert slot_12 in times

        full_slot = next(s for s in result.availability if s.start_time == slot_11)
        assert full_slot.is_available is False
        assert full_slot.current_occupancy == 2

        partial_slot = next(s for s in result.availability if s.start_time == slot_12)
        assert partial_slot.is_available is True
        assert partial_slot.current_occupancy == 1
        assert partial_slot.max_slots == 2

def test_get_availability_empty_occupancy_shows_all_slots(availability_svc, mock_uow):
    service = make_service(max_slots=1)
    mock_uow.service_repo.get_by_id.return_value = service
    
    profesional = MagicMock()
    profesional.id = 1
    profesional.buffer_minutes = 0
    profesional.public_link = "test-profesional"
    service.profesional = profesional

    mock_ws = []
    for d in range(7):
        ws = MagicMock(spec=WeeklySchedule)
        ws.day_of_week = d
        ws.start_time = time(9, 0)
        ws.end_time = time(18, 0)
        mock_ws.append(ws)
    mock_uow.weekly_schedule_repo.get_by_profesional.return_value = mock_ws
    mock_uow.schedule_block_repo.get_blocks_in_range.return_value = []
    mock_uow.appointment_repo.get_occupancy_by_service.return_value = []

    test_now = datetime(2026, 5, 20, 10, 30)
    with patch('app.services.availability_service.datetime') as mock_dt:
        mock_dt.now.return_value = test_now
        mock_dt.combine = datetime.combine
        mock_dt.date = datetime.date
        result = availability_svc.get_service_availability(service.id, days=1)

        assert len(result.availability) > 0
        for slot in result.availability:
            assert slot.current_occupancy == 0
            assert slot.max_slots == 1
