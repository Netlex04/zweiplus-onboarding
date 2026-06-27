"""Import orchestration (FR-INT-001..006): canonical -> adapter -> ImportJob.

Bridges the canonical service and the ``TargetAdapter`` seam and drives the
``ImportJob`` state machine. No HTTP here — the imports router calls in.

Gate (FR-REV-003): an import may only be prepared/created once the module is
``completed`` or ``import_ready`` (i.e. review-approved).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import CanonicalOutput, ImportJob, ModuleInstance
from app.models.enums import ImportStatus, ModuleStatus
from app.providers.target import ImportPreview, get_target_adapter
from app.services import canonical
from app.services.statemachine import (
    assert_import_transition,
    assert_module_transition,
)

# Module statuses from which an import may be prepared/created (FR-REV-003).
_IMPORT_ALLOWED = {
    ModuleStatus.COMPLETED.value,
    ModuleStatus.IMPORT_READY.value,
    ModuleStatus.IMPORTED.value,
}


class ImportNotAllowed(Exception):
    """Raised when an import is requested for a non-released module (-> 409)."""


def _ensure_canonical(session: Session, module: ModuleInstance) -> CanonicalOutput:
    """Return the canonical output for the module, building it if missing."""
    return canonical.build_canonical(session, module)


def build_preview(
    session: Session, module: ModuleInstance, target_system: str
) -> ImportPreview:
    """Build (or refresh) canonical + return the adapter's import preview.

    Marks the module ``import_ready`` when it is ``completed`` (preview implies
    the module is ready to be staged for import).
    """
    canon = _ensure_canonical(session, module)
    adapter = get_target_adapter(target_system)
    preview = adapter.preview(canon.data or {})

    if module.status == ModuleStatus.COMPLETED.value:
        assert_module_transition(module.status, ModuleStatus.IMPORT_READY)
        module.status = ModuleStatus.IMPORT_READY.value
    session.flush()
    return preview


def create_import_job(
    session: Session, module: ModuleInstance, target_system: str
) -> ImportJob:
    """Create an ImportJob in ``mapping_ready`` with mapped payload + preview.

    Raises ``ImportNotAllowed`` if the module is not released yet.
    """
    if module.status not in _IMPORT_ALLOWED:
        raise ImportNotAllowed(
            f"Modul {module.id} ist nicht freigegeben (Status {module.status})."
        )

    canon = _ensure_canonical(session, module)
    adapter = get_target_adapter(target_system)
    payload = adapter.map(canon.data or {})
    preview = adapter.preview(canon.data or {})

    job = ImportJob(
        module_instance_id=module.id,
        target_system=target_system,
        status=ImportStatus.NOT_PREPARED.value,
        mapped_payload=payload,
        preview=preview.to_dict(),
        errors=preview.errors,
    )
    assert_import_transition(job.status, ImportStatus.MAPPING_READY)
    job.status = ImportStatus.MAPPING_READY.value
    session.add(job)

    if module.status == ModuleStatus.COMPLETED.value:
        assert_module_transition(module.status, ModuleStatus.IMPORT_READY)
        module.status = ModuleStatus.IMPORT_READY.value
    session.flush()
    return job


def run_import_job(session: Session, job: ImportJob) -> ImportJob:
    """Drive the ImportJob through validated->approved->importing->imported.

    On adapter failure the job ends in ``import_failed`` and the module stays
    put. On success the module transitions to ``imported``.
    """
    adapter = get_target_adapter(job.target_system)

    # mapping_ready -> validated -> approved -> importing
    for nxt in (
        ImportStatus.VALIDATED,
        ImportStatus.APPROVED,
        ImportStatus.IMPORTING,
    ):
        assert_import_transition(job.status, nxt)
        job.status = nxt.value
    session.flush()

    result = adapter.run_import(job.mapped_payload or {})
    if not result.success:
        assert_import_transition(job.status, ImportStatus.IMPORT_FAILED)
        job.status = ImportStatus.IMPORT_FAILED.value
        job.errors = result.errors or ["Import fehlgeschlagen."]
        session.flush()
        return job

    assert_import_transition(job.status, ImportStatus.IMPORTED)
    job.status = ImportStatus.IMPORTED.value
    job.errors = []

    module = session.get(ModuleInstance, job.module_instance_id)
    if module is not None and module.status != ModuleStatus.IMPORTED.value:
        assert_module_transition(module.status, ModuleStatus.IMPORTED)
        module.status = ModuleStatus.IMPORTED.value
    session.flush()
    return job
