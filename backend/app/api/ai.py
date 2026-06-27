"""AI router: chat, suggest, validate, analyze-document (Architektur §6/§8).

All endpoints require authentication. The AI provider is injected via the
``provider_dependency`` so tests can override it with a deterministic stub.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import current_user
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import AiSuggestion, AiValidationResult, User
from app.providers.ai import AiProvider, get_ai_provider
from app.providers.storage import FileStorage, get_storage
from app.schemas import (
    AiChatRequest,
    AiChatResponse,
    AiSuggestionOut,
    AiSuggestRequest,
    AiValidateRequest,
    AiValidationResultOut,
    AnalyzeDocumentRequest,
)
from app.services import ai_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


def provider_dependency(settings: Settings = Depends(get_settings)) -> AiProvider:
    """FastAPI dependency yielding the configured AI provider.

    Overridable in tests via ``app.dependency_overrides[provider_dependency]``.
    """
    return get_ai_provider(settings)


def storage_dependency(settings: Settings = Depends(get_settings)) -> FileStorage:
    return get_storage(settings)


def _suggestion_out(suggestion: AiSuggestion) -> AiSuggestionOut:
    payload = suggestion.payload or {}
    return AiSuggestionOut(
        id=suggestion.id,
        suggestion_type=suggestion.suggestion_type,
        module_id=suggestion.module_instance_id,
        step_id=suggestion.step_instance_id,
        question_id=suggestion.question_def_id,
        proposed_value=payload.get("proposedValue"),
        confidence=suggestion.confidence,
        requires_review=suggestion.requires_review,
        open_questions=suggestion.open_questions or [],
        source_upload_id=suggestion.source_upload_id,
    )


def _validation_out(result: AiValidationResult) -> AiValidationResultOut:
    return AiValidationResultOut(
        id=result.id,
        passed=result.passed,
        checks=result.checks or [],
        issues=result.issues or [],
    )


@router.post("/chat", response_model=AiChatResponse)
def ai_chat(
    payload: AiChatRequest,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
    provider: AiProvider = Depends(provider_dependency),
) -> AiChatResponse:
    reply = ai_service.run_chat(
        session,
        provider,
        context=payload.context,
        context_ref=payload.context_ref,
        message=payload.message,
        history=[m.model_dump() for m in payload.history],
    )
    return AiChatResponse(reply=reply)


@router.post("/suggest", response_model=AiSuggestionOut)
def ai_suggest(
    payload: AiSuggestRequest,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
    provider: AiProvider = Depends(provider_dependency),
) -> AiSuggestionOut:
    try:
        suggestion = ai_service.run_suggest(
            session,
            provider,
            step_instance_id=payload.step_instance_id,
            question_key=payload.question_key,
        )
    except ai_service.AiServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.commit()
    session.refresh(suggestion)
    return _suggestion_out(suggestion)


@router.post("/validate", response_model=AiValidationResultOut)
def ai_validate(
    payload: AiValidateRequest,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
    provider: AiProvider = Depends(provider_dependency),
) -> AiValidationResultOut:
    try:
        result = ai_service.run_validate(
            session, provider, step_instance_id=payload.step_instance_id
        )
    except ai_service.AiServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.commit()
    session.refresh(result)
    return _validation_out(result)


@router.post("/analyze-document", response_model=AiSuggestionOut)
def ai_analyze_document(
    payload: AnalyzeDocumentRequest,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
    provider: AiProvider = Depends(provider_dependency),
    storage: FileStorage = Depends(storage_dependency),
) -> AiSuggestionOut:
    try:
        suggestion = ai_service.run_analyze_document(
            session, provider, storage, upload_id=payload.upload_id
        )
    except ai_service.AiServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.commit()
    session.refresh(suggestion)
    return _suggestion_out(suggestion)
