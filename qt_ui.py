"""
Native PyQt6 UI for Study Tracker calendar.
Replaces the HTML/JS webview with pure Qt widgets.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Optional

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QGridLayout, QScrollArea, QFrame, QColor, QFont, Qt, QCalendarWidget,
    QDateEdit, QDate, QMessageBox, QThread, pyqtSignal
)

from . import sync, tracker


class SyncWorker(QThread):
    """Background worker for git sync to prevent UI freezing."""
    finished = pyqtSignal(bool, str)

    def run(self):
        ok, msg = sync.push_my_data()
        self.finished.emit(ok, msg)


class DayCell(QFrame):
    """A single day cell in the calendar grid."""

    def __init__(self, date_obj: Optional[datetime], friends_data: list, parent=None):
        super().__init__(parent)
        self.date_obj = date_obj
        self.friends_data = friends_data
        self.selected = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 12px;
                background: #18181f;
            }
            QFrame:hover {
                border-color: rgba(255,255,255,0.14);
                background: #22222c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 7)
        layout.setSpacing(4)

        if date_obj:
            # Date number
            day_label = QLabel(str(date_obj.day))
            day_label.setStyleSheet("""
                color: #9090a8;
                font-size: 12px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            """)
            layout.addWidget(day_label)

            # Avatars container
            avatar_layout = QHBoxLayout()
            avatar_layout.setSpacing(3)
            avatar_layout.setContentsMargins(0, 0, 0, 0)

            date_str = date_obj.strftime("%Y-%m-%d")
            for friend in friends_data:
                reviews = friend.get("reviews", {})
                if date_str in reviews and reviews[date_str] > 0:
                    av = self._make_avatar(friend["name"], friend.get("color", "#378ADD"))
                    avatar_layout.addWidget(av)

            avatar_layout.addStretch()
            layout.addLayout(avatar_layout)

            # Progress bar
            layout.addSpacing(2)
            total_studied = sum(1 for f in friends_data if date_str in f.get("reviews", {}) and f["reviews"][date_str] > 0)
            if total_studied > 0 and friends_data:
                progress_pct = (total_studied / len(friends_data)) * 100
                progress_bar = QLabel()
                progress_bar.setStyleSheet(f"""
                    background: linear-gradient(to right, #7c6af7 {progress_pct}%, #22222c {progress_pct}%);
                    height: 2px;
                    border-radius: 2px;
                """)
                layout.addWidget(progress_bar)

            layout.addStretch()
        else:
            layout.addStretch()

        self.setMinimumHeight(88)

    def _make_avatar(self, name: str, color: str) -> QLabel:
        """Create an avatar label."""
        avatar = QLabel(name[0].upper() if name else "?")
        avatar.setStyleSheet(f"""
            background: {color};
            color: white;
            border-radius: 11px;
            width: 22px;
            height: 22px;
            font-weight: bold;
            font-size: 9px;
            text-align: center;
            line-height: 22px;
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return avatar

    def set_selected(self, selected: bool):
        """Highlight this cell as selected."""
        self.selected = selected
        if selected:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #a594f9;
                    border-radius: 12px;
                    background: #22222c;
                    box-shadow: 0 0 0 1px #a594f9;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid rgba(255,255,255,0.07);
                    border-radius: 12px;
                    background: #18181f;
                }
                QFrame:hover {
                    border-color: rgba(255,255,255,0.14);
                    background: #22222c;
                }
            """)


class CalendarPanel(QWidget):
    """Left panel with calendar grid."""

    cell_clicked = pyqtSignal(object)  # emits datetime or None

    def __init__(self, friends_data: list, parent=None):
        super().__init__(parent)
        self.friends_data = friends_data
        self.current_date = datetime.now()
        self.selected_cell = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Navigation bar
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("‹")
        self.prev_btn.setMaximumWidth(36)
        self.prev_btn.setMaximumHeight(36)
        self.prev_btn.clicked.connect(self._prev_month)

        self.next_btn = QPushButton("›")
        self.next_btn.setMaximumWidth(36)
        self.next_btn.setMaximumHeight(36)
        self.next_btn.clicked.connect(self._next_month)

        self.month_label = QLabel()
        self.month_label.setStyleSheet("font-size: 22px; font-weight: 600;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.today_btn = QPushButton("Hôm nay")
        self.today_btn.setMaximumHeight(36)
        self.today_btn.clicked.connect(self._go_today)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.month_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.today_btn)
        layout.addLayout(nav_layout)

        # Calendar grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6)

        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            hdr = QLabel(day)
            hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hdr.setStyleSheet("""
                color: #55556a;
                font-size: 11px;
                font-weight: 500;
                text-transform: uppercase;
            """)
            self.grid_layout.addWidget(hdr, 0, i)

        layout.addLayout(self.grid_layout)
        layout.addStretch()

        self._update_calendar()

    def _update_calendar(self):
        """Rebuild calendar grid for current month."""
        # Clear old cells
        for i in reversed(range(1, self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        self.month_label.setText(self.current_date.strftime("%B %Y").capitalize())

        # Get first day of month and number of days
        first_day = self.current_date.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Calculate starting row and column
        start_weekday = first_day.weekday()  # 0=Monday
        row = 1
        col = start_weekday

        # Add cells for previous month (empty)
        for i in range(start_weekday):
            cell = DayCell(None, self.friends_data, self)
            self.grid_layout.addWidget(cell, row, i)

        # Add cells for this month
        for day in range(1, last_day.day + 1):
            date_obj = self.current_date.replace(day=day)
            cell = DayCell(date_obj, self.friends_data, self)
            cell.mousePressEvent = lambda ev, d=date_obj: self._on_cell_clicked(d)
            self.grid_layout.addWidget(cell, row, col)

            col += 1
            if col == 7:
                col = 0
                row += 1

        # Add cells for next month (empty)
        while col < 7:
            cell = DayCell(None, self.friends_data, self)
            self.grid_layout.addWidget(cell, row, col)
            col += 1

    def _prev_month(self):
        self.current_date = (self.current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        self._update_calendar()

    def _next_month(self):
        self.current_date = (self.current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        self._update_calendar()

    def _go_today(self):
        self.current_date = datetime.now()
        self._update_calendar()

    def _on_cell_clicked(self, date_obj: datetime):
        if self.selected_cell:
            self.selected_cell.set_selected(False)
        self.selected_cell = None
        self.cell_clicked.emit(date_obj)

    def set_friends_data(self, friends_data: list):
        """Update friends data and refresh calendar."""
        self.friends_data = friends_data
        self._update_calendar()


class DetailPanel(QWidget):
    """Right panel showing details for selected date."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_date: Optional[datetime] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        self.empty_label = QLabel("선택된 날짜가 없습니다")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #55556a; font-size: 13px;")

        layout.addSpacing(24)
        layout.addWidget(self.empty_label)
        layout.addStretch()

        self.setMinimumWidth(280)
        self.setStyleSheet("""
            QWidget {
                border-left: 1px solid rgba(255,255,255,0.07);
                background: #18181f;
            }
        """)

    def show_date_details(self, date_obj: datetime, friends_data: list):
        """Display details for a specific date."""
        self.selected_date = date_obj

        # Clear previous layout
        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        layout = self.layout()
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setSpacing(0)

        # Date header
        date_str = date_obj.strftime("%Y-%m-%d")
        weekday_str = date_obj.strftime("%A")

        date_label = QLabel(date_str)
        date_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #e8e8f0;")
        layout.addWidget(date_label)

        weekday_label = QLabel(weekday_str)
        weekday_label.setStyleSheet("font-size: 11px; color: #55556a; margin-top: 2px;")
        layout.addWidget(weekday_label)

        layout.addSpacing(12)

        # Stats
        total_friends = len(friends_data)
        studied_today = sum(1 for f in friends_data if date_str in f.get("reviews", {}) and f["reviews"][date_str] > 0)

        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(8)

        stat1 = QFrame()
        stat1.setStyleSheet("background: #22222c; border-radius: 8px; padding: 8px 10px;")
        stat1_layout = QVBoxLayout(stat1)
        stat1_layout.setContentsMargins(8, 8, 8, 8)
        stat1_val = QLabel(str(studied_today))
        stat1_val.setStyleSheet("font-size: 18px; font-weight: 600; color: #e8e8f0; font-family: 'Courier New';")
        stat1_key = QLabel("STUDIED")
        stat1_key.setStyleSheet("font-size: 10px; color: #55556a; margin-top: 2px; text-transform: uppercase;")
        stat1_layout.addWidget(stat1_val)
        stat1_layout.addWidget(stat1_key)
        stats_layout.addWidget(stat1)

        stat2 = QFrame()
        stat2.setStyleSheet("background: #22222c; border-radius: 8px; padding: 8px 10px;")
        stat2_layout = QVBoxLayout(stat2)
        stat2_layout.setContentsMargins(8, 8, 8, 8)
        stat2_val = QLabel(str(total_friends))
        stat2_val.setStyleSheet("font-size: 18px; font-weight: 600; color: #e8e8f0; font-family: 'Courier New';")
        stat2_key = QLabel("GROUP")
        stat2_key.setStyleSheet("font-size: 10px; color: #55556a; margin-top: 2px; text-transform: uppercase;")
        stat2_layout.addWidget(stat2_val)
        stat2_layout.addWidget(stat2_key)
        stats_layout.addWidget(stat2)

        layout.addLayout(stats_layout)
        layout.addSpacing(12)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(255,255,255,0.07);")
        layout.addWidget(divider)

        # Friend list
        layout.addSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

        for friend in friends_data:
            friend_row = self._make_friend_row(friend, date_str)
            scroll_layout.addWidget(friend_row)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def _make_friend_row(self, friend: dict, date_str: str) -> QWidget:
        """Create a friend row in the detail list."""
        row_widget = QWidget()
        row_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-bottom: 1px solid rgba(255,255,255,0.07);
                padding: 10px 0;
            }
            QWidget:hover { background: #22222c; }
        """)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 10, 0, 10)
        row_layout.setSpacing(10)

        # Avatar
        avatar = QLabel(friend["name"][0].upper() if friend.get("name") else "?")
        avatar.setStyleSheet(f"""
            background: {friend.get("color", "#378ADD")};
            color: white;
            border-radius: 11px;
            width: 28px;
            height: 28px;
            font-weight: bold;
            font-size: 11px;
            text-align: center;
            line-height: 28px;
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(avatar)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(friend.get("name", "Unknown"))
        name_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #e8e8f0;")
        info_layout.addWidget(name_label)

        reviews = friend.get("reviews", {}).get(date_str, 0)
        count_label = QLabel(f"{reviews} cards" if reviews > 0 else "—")
        count_label.setStyleSheet("font-size: 11px; color: #9090a8; font-family: 'Courier New';")
        info_layout.addWidget(count_label)

        row_layout.addLayout(info_layout)

        # Badge
        badge_text = "Done" if reviews > 0 else "Miss"
        badge_color = "background: rgba(62,207,142,0.15); color: #3ecf8e;" if reviews > 0 else "background: rgba(255,255,255,0.05); color: #55556a;"
        badge = QLabel(badge_text)
        badge.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 600;
            border-radius: 20px;
            padding: 3px 9px;
            text-transform: uppercase;
            {badge_color}
        """)
        row_layout.addWidget(badge)

        return row_widget


class TrackerWindowQt(QDialog):
    """Main tracker window with native Qt UI."""

    def __init__(self):
        super().__init__(mw)
        self.setWindowTitle("Study Tracker – Group Calendar")
        self.resize(1280, 720)

        self.friends_data: list = []
        self.sync_worker: Optional[SyncWorker] = None

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        topbar = QWidget()
        topbar.setStyleSheet("background: #18181f; border-bottom: 1px solid rgba(255,255,255,0.07);")
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(28, 18, 28, 18)
        topbar_layout.setSpacing(14)

        logo = QLabel("📅")
        logo.setStyleSheet("font-size: 32px;")
        topbar_layout.addWidget(logo)

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(1)
        title_label = QLabel("Study Tracker")
        title_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #e8e8f0;")
        title_layout.addWidget(title_label)
        subtitle_label = QLabel("group.json")
        subtitle_label.setStyleSheet("font-size: 12px; color: #9090a8; font-family: 'Courier New';")
        title_layout.addWidget(subtitle_label)
        topbar_layout.addLayout(title_layout)

        topbar_layout.addStretch()

        self.sync_btn = QPushButton("↻ Sync GitHub")
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background: #7c6af7;
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover { opacity: 0.85; }
            QPushButton:pressed { opacity: 0.7; }
        """)
        self.sync_btn.clicked.connect(self._on_sync_clicked)
        topbar_layout.addWidget(self.sync_btn)

        main_layout.addWidget(topbar)

        # Legend bar
        legend_bar = QWidget()
        legend_bar.setStyleSheet("background: #18181f; border-bottom: 1px solid rgba(255,255,255,0.07); padding: 12px 28px;")
        legend_layout = QHBoxLayout(legend_bar)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(6)
        legend_label = QLabel("MEMBERS")
        legend_label.setStyleSheet("font-size: 11px; color: #55556a; text-transform: uppercase;")
        legend_layout.addWidget(legend_label)
        legend_layout.addStretch()
        main_layout.addWidget(legend_bar)

        # Content area (calendar + detail panel)
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.calendar_panel = CalendarPanel([], self)
        self.calendar_panel.cell_clicked.connect(self._on_cell_clicked)
        content_layout.addWidget(self.calendar_panel)

        self.detail_panel = DetailPanel(self)
        content_layout.addWidget(self.detail_panel)

        main_layout.addWidget(content)

        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("""
            QLabel {
                background: #18181f;
                border-top: 1px solid rgba(255,255,255,0.07);
                padding: 10px 28px;
                font-size: 11px;
                color: #55556a;
                font-family: 'Courier New';
            }
        """)
        main_layout.addWidget(self.status_bar)

        self._load_data()

    def _load_data(self):
        """Load friends data from repo and update UI."""
        self.friends_data = sync.pull_all_data()

        cfg = mw.addonManager.getConfig(__name__) or {}
        my_name = cfg.get("my_name", "Me").strip()
        my_color = cfg.get("my_color", "#378ADD")

        # If our data not in repo, add live data
        names_in_repo = {f.get("name", "") for f in self.friends_data}
        if my_name not in names_in_repo:
            self.friends_data.append({
                "name": my_name,
                "color": my_color,
                "reviews": tracker.get_my_reviews(),
                "last_updated": "",
            })

        self.calendar_panel.set_friends_data(self.friends_data)
        self.status_bar.setText(f"Ready – {len(self.friends_data)} members")

    def _on_cell_clicked(self, date_obj: datetime):
        """Handle calendar cell click."""
        self.detail_panel.show_date_details(date_obj, self.friends_data)

    def _on_sync_clicked(self):
        """Handle sync button click."""
        self.sync_btn.setEnabled(False)
        self.status_bar.setText("Syncing...")

        self.sync_worker = SyncWorker()
        self.sync_worker.finished.connect(self._on_sync_done)
        self.sync_worker.start()

    def _on_sync_done(self, ok: bool, msg: str):
        """Handle sync completion."""
        self.sync_btn.setEnabled(True)
        self.status_bar.setText(f"Synced: {msg}" if ok else f"Sync failed: {msg}")

        if ok:
            self._load_data()
            QMessageBox.information(self, "Study Tracker", msg)
        else:
            QMessageBox.warning(self, "Study Tracker", f"Sync failed:\n{msg}")

    def refresh(self):
        """Refresh data."""
        self._load_data()


def show_tracker_window():
    """Open the tracker window."""
    win = TrackerWindowQt()
    win.exec()
