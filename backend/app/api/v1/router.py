from fastapi import APIRouter

from app.api.v1 import (
    agenda,
    auth,
    availability,
    clientes,
    locales,
    profesionales,
    services,
    users,
    appointments,
    form_fields,
    whatsapp,
    refunds,
    notifications,
)

api_router = APIRouter()

api_router.include_router(clientes.router, prefix="/clientes", tags=["clientes"])
api_router.include_router(
    profesionales.router, prefix="/profesionales", tags=["profesionales"]
)
api_router.include_router(locales.router, prefix="/locales", tags=["locales"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(availability.router, prefix="/availability", tags=["availability"])
api_router.include_router(agenda.router, prefix="/agenda", tags=["agenda"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(form_fields.router, prefix="/form-fields", tags=["form-fields"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(refunds.router, prefix="/refunds", tags=["refunds"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
