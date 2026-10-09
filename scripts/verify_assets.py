"""Verify that a clone contains the complete binary assets, without LFS pointers."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "asset-manifest.json").read_text())
for asset in manifest["files"]:
    path = root / asset["path"]
    assert path.is_file(), f"Missing asset: {path}"
    raw = path.read_bytes()
    assert len(raw) == asset["bytes"], f"Wrong size: {path}"
    assert hashlib.sha256(raw).hexdigest() == asset["sha256"], f"Corrupt asset: {path}"
print(f"ASSETS_OK: {len(manifest['files'])} assets verified")
