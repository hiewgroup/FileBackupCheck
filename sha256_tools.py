"""Utilities for calculating SHA256 hashes across platforms."""

from tkinter import filedialog, messagebox
import os
import platform
import re
import shutil
import subprocess


_seven_zip_exe = None
_windows_method = None


def _choose_windows_method():
    """Ask the user which hashing method to use on Windows."""
    global _windows_method
    if _windows_method:
        return _windows_method

    use_7z = messagebox.askyesno(
        "Hashing Method",
        "Use 7-Zip for hashing?\nSelect No to use certutil instead.",
    )
    _windows_method = "7zip" if use_7z else "certutil"
    return _windows_method


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
            match = re.search(r"\b([0-9a-fA-F]{64})\b", line)
            if match:
                return match.group(1).lower()

        print(f"Warning: SHA256 not found for {filepath}")
        return None
    except Exception as exc:  # pragma: no cover - process execution
        print(f"Exception hashing {filepath}: {exc}")
        return None


def _calculate_with_certutil(filepath):
    """Compute SHA256 using Windows certutil."""
    try:
        result = subprocess.run(
            ["certutil", "-hashfile", filepath, "SHA256"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        if result.returncode != 0:
            print(f"Error hashing {filepath}: {result.stderr.strip()}")
            return None

        for line in result.stdout.splitlines():
            cleaned = line.strip().replace(" ", "")
            if re.fullmatch(r"[0-9a-fA-F]{64}", cleaned):
                return cleaned.lower()

        print(f"Unexpected output format when hashing {filepath}")
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
        method = _choose_windows_method()
        if method == "7zip":
            return _calculate_with_7z(filepath)
        return _calculate_with_certutil(filepath)

    # Prefer sha256sum on Unix-like systems
    if shutil.which("sha256sum"):
        return _calculate_with_sha256sum(filepath)

    # macOS does not always provide sha256sum; use shasum -a 256
    if shutil.which("shasum"):
        return _calculate_with_shasum(filepath)

    print("No suitable SHA256 calculation method found.")
    return None

