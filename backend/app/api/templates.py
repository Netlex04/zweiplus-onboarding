"""Templates router: rendered template + file download."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db.session import get_session
from app.models import TemplateDefinition, User
from app.schemas import TemplateOut
from app.services import templates as template_service

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Minimal extension -> content-type map for generated placeholder files.
_CONTENT_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "txt": "text/plain",
}


def _get_template(session: Session, template_key: str) -> TemplateDefinition:
    template = session.scalar(
        select(TemplateDefinition).where(TemplateDefinition.key == template_key)
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
    return template


@router.get("/{template_key}", response_model=TemplateOut)
def get_template(
    template_key: str,
    moduleInstanceId: str | None = None,
    session: Session = Depends(get_session),
    _user: User = Depends(current_user),
) -> TemplateOut:
    template = _get_template(session, template_key)
    context = template_service.build_context(session, moduleInstanceId)
    return TemplateOut.model_validate(
        template_service.render_template(template, context)
    )


@router.get("/{template_key}/file")
def get_template_file(
    template_key: str,
    session: Session = Depends(get_session),
    _user: User = Depends(current_user),
) -> Response:
    template = _get_template(session, template_key)
    file_name = template.file_name or f"{template.key}.txt"
    file_type = (template.file_type or "txt").lower()
    content_type = _CONTENT_TYPES.get(file_type, "application/octet-stream")

    # No real binary is stored for seeded file templates; generate a readable
    # placeholder so the download flow works end to end (FR-TPL).
    placeholder = (
        f"{template.title}\n\n"
        "Dies ist eine generierte Platzhalter-Datei für diese Vorlage.\n"
        "Bitte ersetzen Sie sie durch das offizielle Dokument.\n"
    )
    return Response(
        content=placeholder.encode("utf-8"),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
