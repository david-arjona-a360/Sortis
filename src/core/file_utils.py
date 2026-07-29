import os
import json
import tempfile
import time


class AtomicWriteError(IOError):
    pass


def atomic_write_json(directory, filename, data, max_retries=3):
    path = os.path.join(directory, filename)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    last_error = None
    for attempt in range(max_retries):
        try:
            tmp = tempfile.NamedTemporaryFile(
                dir=directory, delete=False, suffix=".tmp",
                mode="w", encoding="utf-8"
            )
            try:
                tmp.write(content)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp.close()
                os.replace(tmp.name, path)
            except Exception:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)
                raise
            return
        except (IOError, OSError, PermissionError) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))
    raise AtomicWriteError(
        f"Failed to write {path} after {max_retries} attempts: {last_error}"
    )


def read_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)
