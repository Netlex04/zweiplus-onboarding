"""Uploads router: POST /api/uploads (whitelist), GET /api/uploads/{id}/download."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import assert_step_access, get_step_or_404
from app.auth import current_user
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import FileUpload, QuestionDefinition, StepDefinition, User
from app.providers.storage import get_storage
from app.schemas import FileUploadOut

router = APIRouter(prefix="/api/uploads", tags=["files"])

# Allowed extensions + content types (Annahme A6).
ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "png", "jpg", "jpeg"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
    "application/octet-stream",  # browsers sometimes send this; extension still checked
}


def _extension(name: str) -> str:
    return (name.rsplit(".", 1)[-1] if "." in name else "").lower()


@router.post("", response_model=FileUploadOut, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    stepInstanceId: str = Form(...),
    questionKey: str = Form(...),
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
    settings: Settings = Depends(get_settings),
) -> FileUploadOut:
    step = get_step_or_404(session, stepInstanceId)
    assert_step_access(session, user, step)

    # Resolve the question for this step + key.
    step_def = session.get(StepDefinition, step.step_def_id)
    question = session.scalar(
        select(QuestionDefinition).where(
            QuestionDefinition.step_def_id == step_def.id,
            QuestionDefinition.key == questionKey,
        )
    )
    if question is None:
        raise HTTPException(status_code=404, detail="Frage nicht gefunden")

    ext = _extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS or (
        file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Dateityp nicht erlaubt (.{ext}, {file.content_type})",
        )

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Datei größer als {settings.max_upload_mb} MB",
        )

    storage = get_storage(settings)
    storage_path = storage.save(data, file.filename or "upload")

    upload = FileUpload(
        question_def_id=question.id,
        step_instance_id=step.id,
        original_name=file.filename or "upload",
        content_type=file.content_type,
        size_bytes=len(data),
        storage_path=storage_path,
        uploaded_by=user.email,
    )
    session.add(upload)
    session.commit()
    session.refresh(upload)
    return FileUploadOut(
        id=upload.id,
        original_name=upload.original_name,
        content_type=upload.content_type,
        size_bytes=upload.size_bytes,
        question_key=questionKey,
    )


@router.get("/{upload_id}/download")
def download_file(
    upload_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
    settings: Settings = Depends(get_settings),
) -> Response:
    upload = session.get(FileUpload, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    step = get_step_or_404(session, upload.step_instance_id)
    assert_step_access(session, user, step)

    storage = get_storage(settings)
    try:
        data = storage.load(upload.storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Datei nicht im Storage gefunden")
    return Response(
        content=data,
        media_type=upload.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{upload.original_name}"'
        },
    )
