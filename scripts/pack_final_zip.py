#!/usr/bin/env python3
import os
import sys
import zipfile
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIP_NAME = sys.argv[1] if len(sys.argv) > 1 else "SANADSQUAD_EVIDENCE_FIRST_V2_REMEDIATED_HANDOFF.zip"
TARGET_ZIP = ROOT / ZIP_NAME

INCLUDED_ROOT_FILES = [
    "brand-voice.md",
    "content-types.json",
    "kb.json",
    "plan.json",
    "pyproject.toml",
    "pytest.ini",
    "requirements.txt",
    "run_piece.py",
    "run_week.py",
    "README.md",
    "ARCHITECTURE.md",
    "ACCEPTANCE_MATRIX.md",
    "LIMITATIONS.md",
    "TEST_RESULTS.md",
    "HANDOFF_MANIFEST.txt",
    ".env.example",
    ".gitignore",
    "REFERENCE_AUDIT.md",
    "SANADSQUAD_HISTORY.bundle",
]

INCLUDED_DIRS = [
    "content_pipeline",
    "source_snapshots",
    "instructions",
    "schemas",
    "scripts",
    "tests",
    "audit",
    "output",
    "knowledge",
    "docs",
    "skills",
    "reference-autopost-ai",
    "SANADSQUAD_FINAL_RELATION_VERIFICATION_HANDOFF",
    "SANADSQUAD_RECALL_RECOVERY_HANDOFF",
]

EXCLUDED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
    ".DS_Store",
}

def should_exclude(rel_path: Path) -> bool:
    for part in rel_path.parts:
        if part in EXCLUDED_PARTS or part.endswith(".pyc") or part.endswith(".zip"):
            return True
    return False

def pack():
    if TARGET_ZIP.exists():
        TARGET_ZIP.unlink()
    
    count = 0
    with zipfile.ZipFile(TARGET_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Add root files
        for fname in sorted(INCLUDED_ROOT_FILES):
            fpath = ROOT / fname
            if fpath.exists():
                zf.write(fpath, arcname=fname)
                count += 1
            else:
                print(f"WARNING: Root file {fname} not found!")

        # Add directories
        for dname in sorted(INCLUDED_DIRS):
            dpath = ROOT / dname
            if not dpath.exists():
                print(f"WARNING: Directory {dname} not found!")
                continue
            for root, dirs, files in os.walk(dpath):
                dirs[:] = [d for d in dirs if d not in EXCLUDED_PARTS]
                for f in sorted(files):
                    fpath = Path(root) / f
                    rel = fpath.relative_to(ROOT)
                    if should_exclude(rel):
                        continue
                    zf.write(fpath, arcname=str(rel))
                    count += 1
    
    sha256 = hashlib.sha256(TARGET_ZIP.read_bytes()).hexdigest()
    print(f"Created {ZIP_NAME}: {count} files packed.")
    print(f"Archive Size: {TARGET_ZIP.stat().st_size:,} bytes")
    print(f"SHA-256: {sha256}")

    # Verify integrity with testzip
    with zipfile.ZipFile(TARGET_ZIP, "r") as zf_test:
        bad_file = zf_test.testzip()
        if bad_file is not None:
            raise RuntimeError(f"Corrupt file detected in archive: {bad_file}")
        print("Archive integrity check: PASSED (testzip returned None).")

    # Also create SANADSQUAD_FINAL_CONTENT_YIELD_CLOSURE_HANDOFF.zip if packing remediated
    alt_name = "SANADSQUAD_FINAL_CONTENT_YIELD_CLOSURE_HANDOFF.zip" if ZIP_NAME != "SANADSQUAD_FINAL_CONTENT_YIELD_CLOSURE_HANDOFF.zip" else "SANADSQUAD_EVIDENCE_FIRST_V2_REMEDIATED_HANDOFF.zip"
    alt_zip = ROOT / alt_name
    import shutil
    shutil.copy2(TARGET_ZIP, alt_zip)
    alt_sha = hashlib.sha256(alt_zip.read_bytes()).hexdigest()
    print(f"Also created {alt_name}: {alt_zip.stat().st_size:,} bytes | SHA-256: {alt_sha}")

if __name__ == "__main__":
    pack()
