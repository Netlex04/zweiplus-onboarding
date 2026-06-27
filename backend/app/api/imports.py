"""Import + canonical router (reviewer/admin): canonical, preview, jobs.

Endpoints (FR-INT-001..006):
- POST /api/modules/{id}/canonical        -> build/return CanonicalOutput
- POST /api/modules/{id}/import-preview   -> adapter preview (ImportPreview)
- POST /api/import-jobs                    -> create ImportJob (mapping_ready)
- POST /api/import-jobs/{id}/run           -> run ImportJob state machine

Import/canonical are gated to released modules (review approved); see
``canonical``/``import_service``. Customers receive 403.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_module_or_404
from app.auth import require_role
from app.db.session import get_session
from app.models import ImportJob, User
from app.models.enums import Role
from app.providers.target import UnknownTargetSystem
from app.schemas import (
    CanonicalOutputOut,
    CreateImportJobRequest,
    ImportJobOut,
    ImportPreviewOut,
    ImportPreviewRequest,
)
from app.services import canonical, import_service

router = APIRouter(tags=["import"])

_reviewer = require_role(Role.REVIEWER, Role.ADMIN)


def _job_dto(job: ImportJob) -> dict:
    return {
        "id": job.id,
        "module_instance_id": job.module_instance_id,
        "target_system": job.target_system,
        "status": job.status,
        "preview": job.preview,
        "errors": job.errors or [],
    }


@router.post(
    "/api/modules/{module_instance_id}/canonical",
    response_model=CanonicalOutputOut,
)
def build_canonical(
    module_instance_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> CanonicalOutputOut:
    module = get_module_or_404(session, module_instance_id)
    try:
        canon = canonical.build_canonical(session, module)
    except canonical.CanonicalNotAllowed as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    session.commit()
    session.refresh(canon)
    return CanonicalOutputOut.model_validate(
        {
            "module_instance_id": canon.module_instance_id,
            "schema_key": canon.schema_key,
            "data": canon.data or {},
        }
    )


@router.post(
    "/api/modules/{module_instance_id}/import-preview",
    response_model=ImportPreviewOut,
)
def import_preview(
    module_instance_id: str,
    payload: ImportPreviewRequest | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> ImportPreviewOut:
    module = get_module_or_404(session, module_instance_id)
    target_system = payload.target_system if payload else "dpms_v1"
    try:
        preview = import_service.build_preview(session, module, target_system)
    except canonical.CanonicalNotAllowed as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except UnknownTargetSystem as exc:
        raise HTTPException(status_code=400, detail=f"Unbekanntes Zielsystem: {exc}")
    session.commit()
    return ImportPreviewOut.model_validate(preview.to_dict())


@router.post("/api/import-jobs", response_model=ImportJobOut, status_code=201)
def create_import_job(
    payload: CreateImportJobRequest,
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> ImportJobOut:
    module = get_module_or_404(session, payload.module_instance_id)
    try:
        job = import_service.create_import_job(
            session, module, payload.target_system
        )
    except import_service.ImportNotAllowed as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except UnknownTargetSystem as exc:
        raise HTTPException(status_code=400, detail=f"Unbekanntes Zielsystem: {exc}")
    session.commit()
    session.refresh(job)
    return ImportJobOut.model_validate(_job_dto(job))


@router.post("/api/import-jobs/{job_id}/run", response_model=ImportJobOut)
def run_import_job(
    job_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> ImportJobOut:
    job = session.get(ImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Importjob nicht gefunden")
    try:
        job = import_service.run_import_job(session, job)
    except UnknownTargetSystem as exc:
        raise HTTPException(status_code=400, detail=f"Unbekanntes Zielsystem: {exc}")
    session.commit()
    session.refresh(job)
    return ImportJobOut.model_validate(_job_dto(job))
