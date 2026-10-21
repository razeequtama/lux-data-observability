"""API v1 master router assembling domain route endpoints."""

from fastapi import APIRouter

from app.api.v1.datasets import router as datasets_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.validations import router as validations_router

api_v1_router = APIRouter()
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(validations_router)
