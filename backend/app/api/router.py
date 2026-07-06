from fastapi import APIRouter
from app.api.v1 import (
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

api_router = APIRouter()

api_router.include_router(health.router, prefix="/v1/health", tags=["Health"])
api_router.include_router(prescriptions.router, prefix="/v1/prescriptions", tags=["Prescriptions"])
api_router.include_router(prior_auths.router, prefix="/v1/prior-auths", tags=["Prior Authorizations"])
api_router.include_router(patients.router, prefix="/v1/patients", tags=["Patients"])
api_router.include_router(insurance.router, prefix="/v1/insurance", tags=["Insurance"])
api_router.include_router(communications.router, prefix="/v1/communications", tags=["Communications"])
api_router.include_router(appeals.router, prefix="/v1/appeals", tags=["Appeals"])
api_router.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
api_router.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])
api_router.include_router(webhooks.router, prefix="/v1/webhooks", tags=["Webhooks"])
api_router.include_router(agents.router, prefix="/v1/agents", tags=["Agents"])
