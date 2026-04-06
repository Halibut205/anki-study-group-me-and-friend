"""
Anki Study Tracker
==================
Group study progress calendar with GitHub sync.

Config keys (Tools → Add-ons → Config):
  my_name      : your display name, e.g. "Ban"
  my_color     : hex colour for your avatar, e.g. "#378ADD"
  repo_path    : absolute path to the cloned shared GitHub repo
                 e.g. "/Users/ban/anki-study-group"
                 or   "C:\\Users\\ban\\anki-study-group"
"""

from aqt import mw
from aqt.qt import QAction
from aqt.utils import qconnect, showWarning

from . import sync, qt_ui


# ── Menu item ────────────────────────────────────────────────────────────────

def _open_tracker():
    qt_ui.show_tracker_window()


action = QAction("Study Tracker 📅", mw)
qconnect(action.triggered, _open_tracker)
mw.form.menuTools.addAction(action)


# ── Auto-sync after Anki sync ────────────────────────────────────────────────

def _after_anki_sync():
    cfg = mw.addonManager.getConfig(__name__) or {}
    if not cfg.get("my_name") or not cfg.get("repo_path"):
        return  # not configured yet, skip silently
    ok, msg = sync.push_my_data()
    if not ok:
        showWarning(f"Study Tracker sync failed:\n{msg}", title="Study Tracker")


try:
    from anki.hooks import sync_did_finish
    sync_did_finish.append(_after_anki_sync)
except ImportError:
    pass  # older Anki version
