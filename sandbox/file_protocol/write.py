# save_sedivis.py
# Backend code – no Qt dependencies

import json
import zipfile
from pathlib import Path
from datetime import datetime, timezone


def create_minimal_sedivis(path: Path) -> None:
    """Create a minimal .sedivis project file."""

    manifest = {
        "format": "sedivis-project",
        "format_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": {
            "project": "project.json",
            "workspace": "workspace.json",
        },
    }

    project = {
        "schema_version": 1,
        "cores": {},
        "analyses": {},
        "images": {},
    }

    workspace = {
        "schema_version": 1,
        "layout": {
            "tabs": [],
            "active_tab_index": 0,
            "sidebar_collapsed": False,
        },
    }

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write zip container
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2))
        z.writestr("project.json", json.dumps(project, indent=2))
        z.writestr("workspace.json", json.dumps(workspace, indent=2))


def get_next_untitled_path(directory: Path) -> Path:
    """Find the next available untitled filename."""
    directory.mkdir(parents=True, exist_ok=True)
    
    # Check if untitled.sedivis exists
    base_path = directory / "untitled.sedivis"
    if not base_path.exists():
        return base_path
    
    # Find the next available number
    counter = 2
    while True:
        path = directory / f"untitled{counter}.sedivis"
        if not path.exists():
            return path
        counter += 1


if __name__ == "__main__":
    files_dir = Path(__file__).parent / "files"
    file_path = get_next_untitled_path(files_dir)
    create_minimal_sedivis(file_path)
    print(f"Created: {file_path.resolve()}")