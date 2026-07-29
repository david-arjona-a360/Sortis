import os
import glob

ONEDRIVE_ORG = "a360inc"
FLOOR_PLAN_FOLDER = "PTY Files - Documents"
FLOOR_PLAN_SUBFOLDER = "FLOOR PLAN"


def get_windows_username():
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"


def _try_find_onedrive_root():
    onedrive_env = os.environ.get("OneDriveCommercial") or os.environ.get("OneDriveConsumer")
    if onedrive_env and os.path.isdir(onedrive_env):
        return onedrive_env

    m1_home = os.path.expanduser("~")
    p1 = os.path.join(m1_home, f"OneDrive - {ONEDRIVE_ORG}*")
    matches1 = glob.glob(p1)
    if matches1 and os.path.isdir(matches1[0]):
        return matches1[0]

    m2_profile = os.environ.get("USERPROFILE")
    if m2_profile:
        p2 = os.path.join(m2_profile, f"OneDrive - {ONEDRIVE_ORG}*")
        matches2 = glob.glob(p2)
        if matches2 and os.path.isdir(matches2[0]):
            return matches2[0]

    fallback_path = rf"C:\Users\{get_windows_username()}\OneDrive - {ONEDRIVE_ORG}"
    if os.path.isdir(fallback_path):
        return fallback_path

    return None


def find_onedrive_root():
    return _try_find_onedrive_root()


def get_floor_plan_path():
    root = find_onedrive_root()
    if root:
        return os.path.join(root, FLOOR_PLAN_FOLDER, FLOOR_PLAN_SUBFOLDER)
    return None


def get_positions_path():
    base = get_floor_plan_path()
    if base:
        return os.path.join(base, "positions.json")
    return None


def get_requests_path():
    base = get_floor_plan_path()
    if base:
        return os.path.join(base, "requests")
    return None


def get_logs_path():
    base = get_floor_plan_path()
    if base:
        return os.path.join(base, "logs")
    return None
