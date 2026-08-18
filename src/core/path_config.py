import os
import glob
import re
import subprocess
import tempfile

ONEDRIVE_ORG = "a360inc"
FLOOR_PLAN_FOLDER = "PTY Files - Documents"
FLOOR_PLAN_SUBFOLDER = "FLOOR PLAN"

# Test-only override: when set, find_onedrive_root() returns this value
# verbatim (no existence check). Used by tests to simulate a missing
# OneDrive root without touching the real discovery logic.
_ONEDRIVE_OVERRIDE_ENV = "SORTIS_ONEDRIVE_OVERRIDE"

_DIAG_LOG = os.path.join(tempfile.gettempdir(), "sortis_diag.log")


def _log_diag(message):
    try:
        with open(_DIAG_LOG, "a", encoding="utf-8") as fh:
            fh.write(message + "\n")
    except OSError:
        pass


def get_windows_username():
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"


def _try_find_onedrive_root():
    override = os.environ.get(_ONEDRIVE_OVERRIDE_ENV)
    if override:
        _log_diag(f"[sortis] {_ONEDRIVE_OVERRIDE_ENV} set -> {override}")
        return override

    methods = []

    onedrive_env = os.environ.get("OneDriveCommercial") or os.environ.get("OneDriveConsumer")
    if onedrive_env and os.path.isdir(onedrive_env):
        methods.append(("onedrive-env", onedrive_env))

    m1_home = os.path.expanduser("~")
    p1 = os.path.join(m1_home, f"OneDrive - {ONEDRIVE_ORG}*")
    matches1 = glob.glob(p1)
    if matches1 and os.path.isdir(matches1[0]):
        methods.append(("expanduser+glob", matches1[0]))

    m2_profile = os.environ.get("USERPROFILE")
    if m2_profile:
        p2 = os.path.join(m2_profile, f"OneDrive - {ONEDRIVE_ORG}*")
        matches2 = glob.glob(p2)
        if matches2 and os.path.isdir(matches2[0]):
            methods.append(("userprofile+glob", matches2[0]))

    real_profile = _get_real_user_profile()
    if real_profile:
        p4 = os.path.join(real_profile, f"OneDrive - {ONEDRIVE_ORG}*")
        matches4 = glob.glob(p4)
        if matches4 and os.path.isdir(matches4[0]):
            methods.append(("real-profile+glob", matches4[0]))

    m3_homedrive = os.environ.get("HOMEDRIVE", "")
    m3_homepath = os.environ.get("HOMEPATH", "")
    if m3_homedrive and m3_homepath:
        m3_base = os.path.join(m3_homedrive, m3_homepath.lstrip("\\"))
        p3 = os.path.join(m3_base, f"OneDrive - {ONEDRIVE_ORG}*")
        matches3 = glob.glob(p3)
        if matches3 and os.path.isdir(matches3[0]):
            methods.append(("homepath+glob", matches3[0]))

    content_match = _find_onedrive_via_floor_plan_scan()
    if content_match:
        methods.append(("floor-plan-content-scan", content_match))

    fallback_path = rf"C:\Users\{get_windows_username()}\OneDrive - {ONEDRIVE_ORG}"
    if os.path.isdir(fallback_path):
        methods.append(("fallback-username", fallback_path))

    if methods:
        _log_diag(f"[sortis] OneDrive root via {methods[0][0]}: {methods[0][1]}")
        return methods[0][1]

    _log_diag(
        "[sortis] OneDrive root not found (all discovery methods failed). "
        f"USERNAME={os.environ.get('USERNAME', '?')} "
        f"USERPROFILE={os.environ.get('USERPROFILE', '?')} "
        f"HOMEDRIVE={os.environ.get('HOMEDRIVE', '?')} "
        f"HOMEPATH={os.environ.get('HOMEPATH', '?')} "
        f"OneDriveCommercial={os.environ.get('OneDriveCommercial', '?')} "
        f"OneDriveConsumer={os.environ.get('OneDriveConsumer', '?')} "
        f"expanduser(~)={os.path.expanduser('~')} "
        f"real_profile={_get_real_user_profile() or '?'}"
    )
    return None


def _get_real_user_profile():
    """Resolve the current user's real profile path from the registry.

    Elevated (Run as administrator) processes can expose a different
    USERPROFILE/HOMEPATH while still belonging to the same user SID; this
    finds the true profile so the OneDrive folder under it is discovered.
    """
    try:
        sid_out = subprocess.run(
            ["whoami", "/user"], capture_output=True, text=True, timeout=5
        ).stdout
        match = re.search(r"S-\d+(-\d+)+", sid_out)
        if not match:
            return None
        import winreg

        key_path = (
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\\"
            + match.group(0)
        )
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            profile, _ = winreg.QueryValueEx(key, "ProfileImagePath")
        return profile if profile and os.path.isdir(profile) else None
    except Exception:
        return None


def _find_onedrive_via_floor_plan_scan():
    """Scan all local user profiles for a OneDrive that contains the map.

    Handles the case where the app runs elevated under a different admin
    account (so USERPROFILE points elsewhere) or where the org folder name
    differs. Only folders that actually contain the FLOOR PLAN data are
    considered, so a consumer OneDrive is never picked by accident.
    """
    system_drive = os.environ.get("SystemDrive", "C:")
    users_root = os.path.join(system_drive, os.sep, "Users")
    if not os.path.isdir(users_root):
        return None

    candidates = []
    for user_dir in glob.glob(os.path.join(users_root, "*")):
        if not os.path.isdir(user_dir):
            continue
        for root in glob.glob(os.path.join(user_dir, "OneDrive*")):
            if not os.path.isdir(root):
                continue
            floor_plan = os.path.join(root, FLOOR_PLAN_FOLDER, FLOOR_PLAN_SUBFOLDER)
            if os.path.isdir(floor_plan):
                candidates.append(root)

    def _prefer_org(root):
        base = os.path.basename(root)
        return 0 if f"OneDrive - {ONEDRIVE_ORG}" in base else 1

    if candidates:
        candidates.sort(key=_prefer_org)
        _log_diag(f"[sortis] floor-plan scan found {len(candidates)} candidate(s)")
        return candidates[0]
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


def get_shared_dept_colors_path():
    base = get_floor_plan_path()
    if base:
        return os.path.join(base, "dept_colors.json")
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
