import uuid
from datetime import datetime, timedelta
from app.core.interfaces.unit_of_work import IUnitOfWork
from app.schemas.availability import ServiceAvailability, SlotAvailability
from app.exceptions.domain_exceptions import ServiceNotFoundError

class AvailabilityService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def get_service_availability(
        self, service_id: uuid.UUID, days: int = 14
    ) -> ServiceAvailability:
        with self.uow:
            service = self.uow.service_repo.get_by_id(service_id)
            if not service or not service.is_active:
                raise ServiceNotFoundError(str(service_id))

            profesional = service.profesional
            if not profesional:
                raise ServiceNotFoundError(str(service_id))

            # Fetch weekly schedule slots & blocks
            weekly_schedules = self.uow.weekly_schedule_repo.get_by_profesional(profesional.id)
            
            now = datetime.now()
            end_search = now + timedelta(days=days)
            
            # Fetch schedule blocks
            blocks = self.uow.schedule_block_repo.get_blocks_in_range(
                profesional.id, now.date(), end_search.date()
            )

            # Fetch occupancy
            occupancy_data = self.uow.appointment_repo.get_occupancy_by_service(
                service_id, now, end_search
            )
            
            # Index occupancy by (year, month, day, hour, minute)
            occupancy = {}
            for dt, count in occupancy_data:
                key = (dt.year, dt.month, dt.day, dt.hour, dt.minute)
                occupancy[key] = count

            available_slots = []
            
            # Generate slots day by day
            for d_idx in range(days + 1):
                current_date = (now + timedelta(days=d_idx)).date()
                
                # Check if date is blocked
                is_blocked = False
                for block in blocks:
                    if block.start_date <= current_date <= block.end_date:
                        is_blocked = True
                        break
                if is_blocked:
                    continue
                
                # Filter weekly schedules for this day
                day_of_week = current_date.weekday()
                day_slots = [ws for ws in weekly_schedules if ws.day_of_week == day_of_week]
                
                for ws in day_slots:
                    ws_start = datetime.combine(current_date, ws.start_time)
                    ws_end = datetime.combine(current_date, ws.end_time)
                    
                    slot_start = ws_start
                    while slot_start + timedelta(minutes=service.duration_minutes) <= ws_end:
                        slot_end = slot_start + timedelta(minutes=service.duration_minutes)
                        
                        # Only show future slots
                        if slot_start > now:
                            occ_key = (slot_start.year, slot_start.month, slot_start.day, slot_start.hour, slot_start.minute)
                            current_occ = occupancy.get(occ_key, 0)
                            is_avail = current_occ < service.max_slots
                            
                            available_slots.append(SlotAvailability(
                                start_time=slot_start,
                                end_time=slot_end,
                                max_slots=service.max_slots,
                                current_occupancy=current_occ,
                                is_available=is_avail
                            ))
                        
                        # Apply buffer minutes
                        slot_start = slot_end + timedelta(minutes=profesional.buffer_minutes)

            public_link = profesional.public_link or str(profesional.user_id)
            return ServiceAvailability(
                service_id=service.id,
                service_name=service.name,
                deposit_active=service.deposit_active,
                deposit_amount=service.deposit_amount,
                deposit_required=service.deposit_required,
                profesional_public_link=public_link,
                availability=available_slots
            )
