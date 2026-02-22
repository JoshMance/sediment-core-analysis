# read_sedivis.py
# Backend code – no Qt dependencies

import json
import zipfile
from pathlib import Path


class SedivisFormatError(Exception):
    pass


def read_sedivis(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)

    with zipfile.ZipFile(path, "r") as z:
        files = set(z.namelist())

        # ---- Required files ----
        required = {"manifest.json", "project.json", "workspace.json"}
        missing = required - files
        if missing:
            raise SedivisFormatError(f"Missing required files: {missing}")

        manifest = json.loads(z.read("manifest.json"))
        project = json.loads(z.read("project.json"))
        workspace = json.loads(z.read("workspace.json"))

    # ---- Basic validation ----
    if manifest.get("format") != "sedivis-project":
        raise SedivisFormatError("Not a sedivis project")

    return {
        "manifest": manifest,
        "project": project,
        "workspace": workspace,
    }


def debug_print(info: dict) -> None:
    print("\nSedivis file contents:")
    print("Format version:", info["manifest"].get("format_version"))
    print("Project schema:", info["project"].get("schema_version"))
    print("Workspace schema:", info["workspace"].get("schema_version"))
    print("Cores:", len(info["project"].get("cores", {})))
    print("Analyses:", len(info["project"].get("analyses", {})))
    print()


if __name__ == "__main__":
    files_dir = Path(__file__).parent / "files"
    
    # List available .sedivis files
    sedivis_files = sorted(files_dir.glob("*.sedivis"))
    
    if not sedivis_files:
        print("No .sedivis files found in files directory")
    else:
        print(f"Found {len(sedivis_files)} .sedivis file(s):")
        for f in sedivis_files:
            print(f"  - {f.name}")
        
        # Read the most recent file
        latest = max(sedivis_files, key=lambda p: p.stat().st_mtime)
        print(f"\nReading: {latest.name}")
        info = read_sedivis(latest)
        debug_print(info)