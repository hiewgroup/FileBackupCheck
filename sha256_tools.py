import subprocess


def calculate_sha256(filepath):
    """Calculate SHA256 hash using Windows certutil."""
    try:
        result = subprocess.run(
            ["certutil", "-hashfile", filepath, "SHA256"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                sha256 = lines[1].strip().replace(' ', '')
                return sha256
            else:
                print(f"Unexpected output format when hashing {filepath}")
                return None
        else:
            print(f"Error hashing {filepath}: {result.stderr.strip()}")
            return None
    except Exception as e:
        print(f"Exception hashing {filepath}: {str(e)}")
        return None
