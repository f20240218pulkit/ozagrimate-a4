"""Build the clean code-repository ZIP for submission.

    python scripts/package_submission.py            -> dist/OzAgriMate_Code_Repository.zip

Includes source, tests, Postman collections, diagrams, docs and evidence summaries.
Excludes git metadata, caches, virtual environments, editor files, local secrets,
private evidence screenshots and previous build output. After building, it extracts
the ZIP to a temporary folder and runs the full test suite there, so the archive is
proven to work on its own.
"""
import fnmatch
import os
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dist", "OzAgriMate_Code_Repository.zip")
TOP = "OzAgriMate"
EXCLUDED_DIRS = {".git", "__pycache__", ".venv", "venv", ".idea", ".vscode", "dist", "node_modules", ".pytest_cache"}
EXCLUDED_FILES = ["*.pyc", "*.pyo", ".env", ".env.*", ".DS_Store", "Thumbs.db", "~$*",
                  "evidence/Postman_Run_*.png", "evidence/Evidence_Record.json"]


def excluded(rel):
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(os.path.basename(rel), p) for p in EXCLUDED_FILES)


def build():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder, dirs, files in os.walk(ROOT):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
            for name in sorted(files):
                path = os.path.join(folder, name)
                rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
                if not excluded(rel):
                    archive.write(path, TOP + "/" + rel)
                    count += 1
    return count


def verify():
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(OUT) as archive:
            archive.extractall(tmp)
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                                cwd=os.path.join(tmp, TOP), capture_output=True, text=True)
        print(result.stderr.strip().splitlines()[-1])
        return result.returncode == 0


if __name__ == "__main__":
    files = build()
    print(f"Wrote {OUT} ({files} files). Verifying extracted copy...")
    sys.exit(0 if verify() else 1)
