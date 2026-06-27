"""TargetAdapter seam (FR-INT-002/003) — canonical -> target-system payload.

Architektur §7 defines ``TargetAdapter`` as the integration seam: each target
system gets one adapter that maps the target-independent *canonical* dict to a
target-specific payload, produces an import preview, and runs the (here:
simulated) import.

Only ``DpmsAdapter`` (target system ``dpms_v1``) is implemented for the MVP
(Annahme A4: Mapping + Vorschau + simulierter Import). Adding a new target
system means adding one ``TargetAdapter`` subclass and registering it in
``_REGISTRY`` — no other code changes.

DPMS target schema (``dpms_v1``)
--------------------------------
A plausible DPMS REST JSON shape with three object kinds. Each mapped object
carries ``objectType`` so the (simulated) DPMS API can dispatch:

- ``softwareSystem``     {objectType, name, notes?}
    from ``software_inventory`` (``used_software`` -> one object per system).
- ``serviceProvider``    {objectType, category, hasDpa, notes?}
    from ``avv_onboarding`` (``processor_categories`` -> one per category;
    ``has_processors`` -> ``hasDpa``).
- ``processingActivity`` {objectType, name, thirdCountryTransfer?,
                          thirdCountryDetails?, securityMeasures?, encryption?}
    aggregated from ``software_inventory`` (third-country) and
    ``tom_erfassung`` (access/encryption) into one Verarbeitungstätigkeit.

Mapping rules + intentionally unmapped fields are documented inline below and in
``backend/README.md`` / ``docs/architekturdokument.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImportPreview:
    """Result of ``TargetAdapter.preview`` (mirrors OpenAPI ``ImportPreview``)."""

    target_system: str
    mapped_objects: list[dict[str, Any]] = field(default_factory=list)
    unmapped_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "targetSystem": self.target_system,
            "mappedObjects": self.mapped_objects,
            "unmappedFields": self.unmapped_fields,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass
class ImportResult:
    """Result of ``TargetAdapter.run_import``."""

    success: bool
    imported_object_count: int = 0
    errors: list[str] = field(default_factory=list)
    detail: str | None = None


class TargetAdapter(ABC):
    """Seam for mapping canonical output onto a concrete target system."""

    target_system: str = ""

    @abstractmethod
    def map(self, canonical: dict) -> dict:
        """Map a canonical dict to the target-specific payload."""

    @abstractmethod
    def preview(self, canonical: dict) -> ImportPreview:
        """Produce an import preview (mapped objects, unmapped, warnings, errors)."""

    @abstractmethod
    def run_import(self, payload: dict) -> ImportResult:
        """Run the import for an already-mapped payload (simulated in MVP)."""


# Canonical question keys that are deliberately NOT mapped to DPMS objects.
# Free-text notes carry no structured DPMS target field; surfaced as
# ``unmappedFields`` so a reviewer sees what was dropped.
_DPMS_UNMAPPED_KEYS = {
    "additional_notes",
    "backup_concept",
    "avv_notes",
    "software_contract_upload",
    "avv_document_upload",
}


class DpmsAdapter(TargetAdapter):
    """Maps canonical output to DPMS-compatible JSON (target ``dpms_v1``)."""

    target_system = "dpms_v1"

    def map(self, canonical: dict) -> dict:
        answers: dict[str, Any] = canonical.get("answers", {}) or {}
        module_name = canonical.get("moduleName")
        objects: list[dict[str, Any]] = []

        # --- softwareSystem objects (software_inventory) ------------------
        used_software = answers.get("used_software")
        if isinstance(used_software, list):
            for name in used_software:
                objects.append({"objectType": "softwareSystem", "name": name})

        # --- serviceProvider objects (avv_onboarding) --------------------
        has_processors = answers.get("has_processors")
        processor_categories = answers.get("processor_categories")
        if isinstance(processor_categories, list):
            for category in processor_categories:
                objects.append(
                    {
                        "objectType": "serviceProvider",
                        "category": category,
                        "hasDpa": has_processors == "ja",
                    }
                )

        # --- processingActivity object (third-country + TOM) -------------
        activity: dict[str, Any] = {}
        third_country = answers.get("third_country")
        if third_country is not None:
            activity["thirdCountryTransfer"] = third_country == "ja"
            details = answers.get("third_country_details")
            if details:
                activity["thirdCountryDetails"] = details
        access_measures = answers.get("access_control_measures")
        if isinstance(access_measures, list) and access_measures:
            activity["securityMeasures"] = access_measures
        encryption = answers.get("encryption_in_use")
        if encryption is not None:
            activity["encryption"] = encryption
        if activity:
            activity = {
                "objectType": "processingActivity",
                "name": module_name or "Verarbeitungstätigkeit",
                **activity,
            }
            objects.append(activity)

        return {"targetSystem": self.target_system, "objects": objects}

    def preview(self, canonical: dict) -> ImportPreview:
        payload = self.map(canonical)
        objects = payload.get("objects", [])

        answers: dict[str, Any] = canonical.get("answers", {}) or {}
        unmapped = [k for k in answers if k in _DPMS_UNMAPPED_KEYS]

        warnings: list[str] = []
        errors: list[str] = []

        if not objects:
            warnings.append(
                "Keine DPMS-Objekte aus den Antworten ableitbar — "
                "Modul enthält keine mapbaren Felder."
            )
        for key in unmapped:
            warnings.append(
                f"Feld '{key}' wird von DPMS nicht strukturiert übernommen "
                f"(nur als Freitext/Anhang verfügbar)."
            )
        # Plausibility: third-country transfer without legal basis details.
        if answers.get("third_country") == "ja" and not answers.get(
            "third_country_details"
        ):
            warnings.append(
                "Drittlandübermittlung ohne Angabe der Rechtsgrundlage."
            )

        return ImportPreview(
            target_system=self.target_system,
            mapped_objects=objects,
            unmapped_fields=unmapped,
            warnings=warnings,
            errors=errors,
        )

    def run_import(self, payload: dict) -> ImportResult:
        # Simulated: no real DPMS REST call (Annahme A4). A payload with no
        # objects is treated as a failed import (nothing to transfer).
        objects = payload.get("objects", []) if isinstance(payload, dict) else []
        if not objects:
            return ImportResult(
                success=False,
                errors=["Leeres Mapping — kein Objekt zum Importieren."],
            )
        return ImportResult(
            success=True,
            imported_object_count=len(objects),
            detail=f"{len(objects)} Objekt(e) simuliert nach DPMS importiert.",
        )


_REGISTRY: dict[str, type[TargetAdapter]] = {
    DpmsAdapter.target_system: DpmsAdapter,
}


class UnknownTargetSystem(Exception):
    """Raised when no adapter is registered for the requested target system."""


def get_target_adapter(target_system: str) -> TargetAdapter:
    """Return the adapter instance for ``target_system`` (registry lookup)."""
    adapter_cls = _REGISTRY.get(target_system)
    if adapter_cls is None:
        raise UnknownTargetSystem(target_system)
    return adapter_cls()
