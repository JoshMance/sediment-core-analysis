"""session_archive — read/write .sedivis project archives.

A .sedivis file is a ZIP archive with this internal layout:

    manifest.json          — format identity + version
    session.json           — serialised entities + workspace entries
    assets/
        <id>_core.png      — sidecar pixel data   (one per CoreEntity)

Responsibilities
----------------
- Write the ZIP on save: bundle asset files, rewrite paths to archive-relative
  refs, serialise entities and workspace state.
- Read the ZIP on load: validate manifest, extract to a caller-supplied
  directory, reconstruct entity objects via the registry, resolve asset refs
  to real extracted paths.

This module is stateless. It raises on any structural or validation error;
the AppController decides how to respond.
"""
from __future__ import annotations

import io
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

import imageio.v3 as iio
import numpy as np
import pandas as pd

from src.domain.entities.registry import ENTITY_TYPES
from src.domain.entities.core_entity import CoreEntity
from src.domain.entities.dataset_entity import DatasetEntity
from src.application.workspace_state import WorkspaceEntry

FORMAT_NAME = "sedivis"
FORMAT_VERSION = 1


# ── Custom exceptions ────────────────────────────────────────────────────────

class ArchiveError(Exception):
    """Raised for any structural or validation problem with a .sedivis file."""


# ── Save ─────────────────────────────────────────────────────────────────────

def save(
    archive_path: Path,
    entities: list[object],
    workspace_entries: list[WorkspaceEntry],
) -> None:
    """Write a .sedivis archive to *archive_path*.

    Args:
        archive_path: Destination file path (will be overwritten if it exists).
        entities: All entity instances from the Store.
        workspace_entries: All open WorkspaceEntry records from WorkspaceState.

    Raises:
        ArchiveError: If an entity's required asset file is missing.
    """
    entity_records: list[dict[str, Any]] = []

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:

        # ── manifest ────────────────────────────────────────────────────────
        zf.writestr(
            "manifest.json",
            json.dumps({"format": FORMAT_NAME, "version": FORMAT_VERSION}, indent=2),
        )

        # ── entities ────────────────────────────────────────────────────────
        for entity in entities:
            if isinstance(entity, CoreEntity):
                record = _save_core_entity(entity, zf)
            elif isinstance(entity, DatasetEntity):
                record = _save_dataset_entity(entity, zf)
            else:
                # Future entity types: save via to_dict(), no asset bundling
                record = {
                    "type": type(entity).__name__,
                    "data": entity.to_dict(),
                }
            entity_records.append(record)

        # ── session.json ────────────────────────────────────────────────────
        session = {
            "entities": entity_records,
            "workspace": [e.to_dict() for e in workspace_entries],
        }
        zf.writestr("session.json", json.dumps(session, indent=2))


def _save_core_entity(entity: CoreEntity, zf: zipfile.ZipFile) -> dict:
    """Encode pixel data as PNG, write as sidecar, return session.json record."""
    asset_name = f"assets/{entity.id}_core.png"

    if entity.data is not None:
        buf = io.BytesIO()
        iio.imwrite(buf, entity.data, extension=".png")
        zf.writestr(asset_name, buf.getvalue())
    # If data is None there is nothing to bundle; asset_ref will be None on load.

    d = entity.to_dict()
    d["asset_ref"] = asset_name if entity.data is not None else None
    return {"type": "CoreEntity", "data": d}

def _save_dataset_entity(entity: DatasetEntity, zf: zipfile.ZipFile) -> dict:
    """Write DataFrame as CSV text, return session.json record."""
    asset_name = f"assets/{entity.id}_data.csv"
    if entity.data is not None:
        zf.writestr(asset_name, entity.data.to_csv(index=False))
    d = entity.to_dict()
    d["asset_ref"] = asset_name if entity.data is not None else None
    return {"type": "DatasetEntity", "data": d}



def load(
    archive_path: Path,
    extract_dir: Path,
) -> tuple[list[object], list[WorkspaceEntry]]:
    """Read a .sedivis archive and return reconstructed entities + workspace entries.

    The archive is extracted into *extract_dir*. Returned entities have their
    asset paths rewritten to point at files inside *extract_dir*. Pixel data
    is NOT loaded here — the AppController does that after this call.

    Args:
        archive_path: Path to the .sedivis file.
        extract_dir: Directory to extract the archive contents into.
                     Should be a TemporaryDirectory managed by the AppController.

    Returns:
        (entities, workspace_entries)

    Raises:
        ArchiveError: On missing/corrupt manifest, unsupported version,
                      missing JSON, or missing bundled assets.
    """
    if not archive_path.exists():
        raise ArchiveError(f"Archive not found: {archive_path}")

    try:
        zf = zipfile.ZipFile(archive_path, "r")
    except zipfile.BadZipFile as e:
        raise ArchiveError(f"Not a valid .sedivis archive: {e}") from e

    with zf:
        _validate_manifest(zf)

        # Extract everything so asset paths can be resolved as real file paths
        zf.extractall(extract_dir)

        session = _read_session(zf, archive_path)

    entities = _reconstruct_entities(session["entities"], extract_dir)
    workspace_entries = _reconstruct_workspace(session.get("workspace", []))

    return entities, workspace_entries


def _validate_manifest(zf: zipfile.ZipFile) -> None:
    if "manifest.json" not in zf.namelist():
        raise ArchiveError("Missing manifest.json — not a .sedivis archive.")
    manifest = json.loads(zf.read("manifest.json"))
    if manifest.get("format") != FORMAT_NAME:
        raise ArchiveError(
            f"Unexpected format '{manifest.get('format')}' — expected '{FORMAT_NAME}'."
        )
    version = manifest.get("version")
    if version != FORMAT_VERSION:
        raise ArchiveError(
            f"Unsupported .sedivis version {version} (this app supports v{FORMAT_VERSION})."
        )


def _read_session(zf: zipfile.ZipFile, archive_path: Path) -> dict:
    if "session.json" not in zf.namelist():
        raise ArchiveError(f"Missing session.json in {archive_path.name}.")
    try:
        return json.loads(zf.read("session.json"))
    except json.JSONDecodeError as e:
        raise ArchiveError(f"Corrupt session.json: {e}") from e


def _reconstruct_entities(records: list[dict], extract_dir: Path) -> list[object]:
    entities = []
    for record in records:
        type_name = record.get("type")
        data = record.get("data", {})

        if type_name not in ENTITY_TYPES:
            raise ArchiveError(f"Unknown entity type '{type_name}' in session.json.")

        if type_name == "CoreEntity":
            entity = _load_core_entity(data, extract_dir)
        elif type_name == "DatasetEntity":
            entity = _load_dataset_entity(data, extract_dir)
        else:
            entity = ENTITY_TYPES[type_name].from_dict(data)

        entities.append(entity)
    return entities


def _load_core_entity(data: dict, extract_dir: Path) -> CoreEntity:
    """Resolve the sidecar PNG path; pixel data loaded later by AppController."""
    asset_ref = data.get("asset_ref")
    if asset_ref:
        resolved = extract_dir / asset_ref
        if not resolved.exists():
            raise ArchiveError(f"Bundled asset missing after extraction: {asset_ref}")
        data = {**data, "asset_ref": str(resolved)}
    return CoreEntity.from_dict(data)


def _load_dataset_entity(data: dict, extract_dir: Path) -> DatasetEntity:
    """Resolve the sidecar CSV path; DataFrame loaded later by AppController."""
    asset_ref = data.get("asset_ref")
    if asset_ref:
        resolved = extract_dir / asset_ref
        if not resolved.exists():
            raise ArchiveError(f"Bundled asset missing after extraction: {asset_ref}")
        data = {**data, "asset_ref": str(resolved)}
    return DatasetEntity.from_dict(data)


def _reconstruct_workspace(records: list[dict]) -> list[WorkspaceEntry]:
    return [WorkspaceEntry.from_dict(r) for r in records]
