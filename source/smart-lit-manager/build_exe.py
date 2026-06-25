#!/usr/bin/env python3
"""Build script for packaging Smart Literature Manager as a standalone .exe."""

import os
import sys
import shutil

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(APP_DIR, "dist")


def build():
    print("=" * 60)
    print("Building Smart Literature Manager executable...")
    print("=" * 60)

    # Check if PyInstaller is available
    try:
        import PyInstaller
        print("[OK] PyInstaller is available.")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        ret = os.system(f"{sys.executable} -m pip install pyinstaller")
        if ret != 0:
            print("[ERROR] Failed to install PyInstaller.")
            return False

    # Clean old build artifacts
    for folder in ["build", "dist", "*.spec"]:
        path = os.path.join(APP_DIR, folder)
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path, ignore_errors=True)

    # Build command
    os.chdir(APP_DIR)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "SmartLitManager",
        "--icon", os.path.join(APP_DIR, "resources", "app.ico") if os.path.exists(
            os.path.join(APP_DIR, "resources", "app.ico")) else "",
        "--add-data", f"ui{os.pathsep}ui",
        "--add-data", f"app{os.pathsep}app",
        "--hidden-import", "PyQt5.sip",
        "--hidden-import", "fitz",
        "main.py"
    ]
    # Remove empty icon arg
    cmd = [c for c in cmd if c]

    print("\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")

    ret = os.system(" ".join(cmd))
    if ret == 0:
        exe_path = os.path.join(OUTPUT_DIR, "SmartLitManager.exe")
        if os.path.exists(exe_path):
            print(f"\n{'=' * 60}")
            print(f"[SUCCESS] Executable created: {exe_path}")
            print(f"{'=' * 60}")
            return True

    print(f"\n[ERROR] Build failed. Check the output above.")
    return False


if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
