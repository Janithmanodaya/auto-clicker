#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def ensure_pyinstaller():
    try:
        import PyInstaller.__main__ as pi  # type: ignore
        return pi
    except Exception:
        print("PyInstaller not found. Installing...", flush=True)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.3"])
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