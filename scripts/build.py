#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def ensure_pip() -> None:
    try:
        import pip  # type: ignore
        return
    except Exception:
        pass

    print("pip not found. Bootstrapping pip with ensurepip...", flush=True)
    try:
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
    except Exception as e:
        print(f"Failed to bootstrap pip via ensurepip: {e}", flush=True)
        raise

    # Verify pip import works now
    try:
        import pip  # type: ignore
    except Exception as e:  # pragma: no cover
        print(f"pip still not importable after ensurepip: {e}", flush=True)
        raise


def ensure_pyinstaller():
    try:
        import PyInstaller.__main__ as pi  # type: ignore
        return pi
    except Exception:
        print("PyInstaller not found. Installing...", flush=True)
        ensure_pip()
        # Try to minimize disk usage during installation
        try:
            # Purge pip cache to free space (harmless if empty)
            subprocess.run([sys.executable, "-m", "pip", "cache", "purge"], check=False)
            # Upgrade core packaging tools without caching
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "--no-cache-dir", "pip", "wheel", "setuptools"])
            # Install PyInstaller with no cache to reduce space usage
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "pyinstaller"])
        except subprocess.CalledProcessError as e:
            print("Failed to install PyInstaller via pip.", flush=True)
            print("Common causes:", flush=True)
            print("  - No space left on device (clear disk space or pip cache)", flush=True)
            print("  - Network issues or restricted environment", flush=True)
            print("Mitigations:", flush=True)
            print("  - Run: python -m pip cache purge", flush=True)
            print("  - Re-run with environment variable: set PIP_NO_CACHE_DIR=1", flush=True)
            print("  - Ensure the drive containing the virtualenv (.venv) has free space", flush=True)
            raise
        import PyInstaller.__main__ as pi  # type: ignore
        return pi


def main():
    parser = argparse.ArgumentParser(description="Build AutoClick Pro executables using PyInstaller")
    parser.add_argument("--onefile", action="store_true", help="Build one-file executable")
    parser.add_argument("--name", default="AutoClickPro", help="Name of the executable/app")
    parser.add_argument("--console", action="store_true", help="Show console window")
    parser.add_argument("--clean", action="store_true", help="Clean PyInstaller cache and remove temporary files before building")
    args = parser.parse_args()

    pi = ensure_pyinstaller()

    dist = PROJECT_ROOT / "dist"
    build = PROJECT_ROOT / "build"
    dist.mkdir(exist_ok=True)
    build.mkdir(exist_ok=True)

    cli_args: list[str] = []
    cli_args += ["--noconfirm"]
    cli_args += ["--windowed"] if not args.console else []
    if args.clean:
        cli_args += ["--clean"]
    cli_args += [f"--name={args.name}", f"--distpath={dist.as_posix()}", f"--workpath={build.as_posix()}"]

    # Collect packages that ship data/plugins or are commonly missed by static analysis
    import importlib.util
    for pkg in ("PySide6", "cv2", "PIL", "numpy", "pynput", "mss", "keyring", "cryptography", "pytesseract", "jsonschema", "loguru"):
        if importlib.util.find_spec(pkg) is not None:
            cli_args += ["--collect-all", pkg]

    # Optional icon if present
    icon: Path | None = None
    if sys.platform.startswith("win"):
        cand = PROJECT_ROOT / "packaging" / "icons" / "app.ico"
        if cand.exists():
            icon = cand
    elif sys.platform == "darwin":
        cand = PROJECT_ROOT / "packaging" / "icons" / "app.icns"
        if cand.exists():
            icon = cand
    if icon is not None:
        cli_args += [f"--icon={icon.as_posix()}"]

    if args.onefile:
        cli_args += ["--onefile"]

    entry = (PROJECT_ROOT / "run.py").as_posix()
    cli_args += [entry]

    print("Running PyInstaller with args:")
    print("  pyinstaller " + " ".join(cli_args))
    pi.run(cli_args)

    if sys.platform.startswith("win"):
        out = dist / args.name / f"{args.name}.exe"
        if args.onefile:
            out = dist / f"{args.name}.exe"
        print(f"Built: {out}")
    elif sys.platform == "darwin":
        out = dist / f"{args.name}.app"
        print(f"Built: {out}")
    else:
        out_dir = dist / args.name
        print(f"Built directory: {out_dir}")
        if args.onefile:
            out_file = dist / args.name
            if out_file.exists():
                print(f"Built onefile: {out_file}")


if __name__ == "__main__":
    sys.exit(main() or 0)