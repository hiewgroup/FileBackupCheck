"""Utilities for calculating SHA256 hashes across platforms."""

from tkinter import filedialog
import os
import platform
import shutil
import subprocess


_seven_zip_exe = None


def _get_seven_zip_exe():
    """Prompt the user to locate 7z.exe if not already provided."""
    global _seven_zip_exe
    if _seven_zip_exe and os.path.isfile(_seven_zip_exe):
        return _seven_zip_exe

    path = filedialog.askopenfilename(
        title="Locate 7z.exe",
        filetypes=[("7z executable", "7z.exe"), ("Executable", "*.exe")],
    )
    if path:
        _seven_zip_exe = path
    return _seven_zip_exe


def _calculate_with_7z(filepath):
    exe = _get_seven_zip_exe()
    if not exe:
        print("7z.exe not provided. Cannot compute SHA256.")
        return None

    try:
        result = subprocess.run(
            [exe, "h", "-scrcSHA256", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if result.returncode != 0:
            print(f"Error hashing {filepath}: {result.stderr.strip()}")
            return None

        for line in result.stdout.splitlines():
            line = line.strip()
            if len(line) == 64 and all(c in "0123456789abcdefABCDEF" for c in line):
                return line.lower()

        print(f"Warning: SHA256 not found for {filepath}")
        return None
    except Exception as exc:  # pragma: no cover - process execution
        print(f"Exception hashing {filepath}: {exc}")
        return None


def _calculate_with_sha256sum(filepath):
    try:
        result = subprocess.run(
            ["sha256sum", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if result.returncode == 0:
            return result.stdout.split()[0]

        print(f"Error hashing {filepath}: {result.stderr.strip()}")
        return None
    except Exception as exc:  # pragma: no cover - process execution
        print(f"Exception hashing {filepath}: {exc}")
        return None


def _calculate_with_shasum(filepath):
    try:
        result = subprocess.run(
            ["shasum", "-a", "256", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if result.returncode == 0:
            return result.stdout.split()[0]

        print(f"Error hashing {filepath}: {result.stderr.strip()}")
        return None
    except Exception as exc:  # pragma: no cover - process execution
        print(f"Exception hashing {filepath}: {exc}")
        return None


def calculate_sha256(filepath):
    """Calculate SHA256 hash regardless of the host platform."""
    system = platform.system()

    if system == "Windows":
        return _calculate_with_7z(filepath)

    # Prefer sha256sum on Unix-like systems
    if shutil.which("sha256sum"):
        return _calculate_with_sha256sum(filepath)

    # macOS does not always provide sha256sum; use shasum -a 256
    if shutil.which("shasum"):
        return _calculate_with_shasum(filepath)

    print("No suitable SHA256 calculation method found.")
    return None

