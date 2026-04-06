import json
import os

from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QUrl
from aqt.webview import AnkiWebView

from . import sync, tracker


class TrackerWindow(QDialog):
    def __init__(self):
        super().__init__(mw)
        self.setWindowTitle("Study Tracker – Group Calendar")
        self.resize(1000, 720)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web = AnkiWebView(title="study_tracker")
        # Handle JS → Python bridge (Sync button)
        self.web.set_bridge_command(self._on_bridge, self)
        layout.addWidget(self.web)

        self._load()

    def _on_bridge(self, cmd: str):
        if cmd == "study_tracker_sync":
            ok, msg = sync.push_my_data()
            ok_js = "true" if ok else "false"
            msg_js = msg.replace("'", "\\'")
            self.web.eval(f"window.onSyncDone({ok_js}, '{msg_js}')")
            if ok:
                self._load()  # Reload data after successful sync

    # ── load ─────────────────────────────────────────────────────────────────

    def _load(self):
        html_path = os.path.join(os.path.dirname(__file__), "web", "calendar.html")

        # Gather data: friends from repo + our own live data as fallback
        friends = sync.pull_all_data()

        cfg = mw.addonManager.getConfig(__name__) or {}
        my_name = cfg.get("my_name", "Me").strip()
        my_color = cfg.get("my_color", "#378ADD")

        # If our own file not yet pushed, inject live data
        names_in_repo = {f.get("name", "") for f in friends}
        if my_name not in names_in_repo:
            friends.append({
                "name": my_name,
                "color": my_color,
                "reviews": tracker.get_my_reviews(),
                "last_updated": "",
            })

        payload = json.dumps(friends, ensure_ascii=False)

        self.web.load_url(QUrl.fromLocalFile(html_path))
        self.web.page().loadFinished.connect(
            lambda _ok: self.web.eval(f"window.initCalendar({payload})")
        )

    # ── public ───────────────────────────────────────────────────────────────

    def refresh(self):
        self._load()


def show_tracker_window():
    win = TrackerWindow()
    win.exec()
