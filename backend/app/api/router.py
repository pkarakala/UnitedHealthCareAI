from fastapi import APIRouter, Depends

from app.api.v1 import (
    auth,
    health,
    prescriptions,
    prior_auths,
    patients,
    insurance,
    communications,
    appeals,
    analytics,
    documents,
    webhooks,
    agents,
)
from app.security import get_current_user

api_router = APIRouter()

# Public: health (platform checks), auth (login), webhooks (signature-verified)
api_router.include_router(health.router, prefix="/v1/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/v1/auth", tags=["Auth"])
api_router.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])

# Everything else requires a valid bearer token
protected = [Depends(get_current_user)]
api_router.include_router(prescriptions.router, prefix="/v1/prescriptions", tags=["Prescriptions"], dependencies=protected)
api_router.include_router(prior_auths.router, prefix="/v1/prior-auths", tags=["Prior Authorizations"], dependencies=protected)
api_router.include_router(patients.router, prefix="/v1/patients", tags=["Patients"], dependencies=protected)
api_router.include_router(insurance.router, prefix="/v1/insurance", tags=["Insurance"], dependencies=protected)
api_router.include_router(communications.router, prefix="/v1/communications", tags=["Communications"], dependencies=protected)
api_router.include_router(appeals.router, prefix="/v1/appeals", tags=["Appeals"], dependencies=protected)
api_router.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"], dependencies=protected)
api_router.include_router(documents.router, prefix="/v1/documents", tags=["Documents"], dependencies=protected)
api_router.include_router(agents.router, prefix="/v1/agents", tags=["Agents"], dependencies=protected)
