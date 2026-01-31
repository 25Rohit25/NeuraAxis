"""
NEURAXIS AI Service - API v1 Router
"""

from fastapi import APIRouter

from app.api.v1 import auth, diagnosis, health, patients

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(patients.router, prefix="/patients", tags=["Patients"])
router.include_router(diagnosis.router, prefix="/diagnosis", tags=["Diagnosis"])
