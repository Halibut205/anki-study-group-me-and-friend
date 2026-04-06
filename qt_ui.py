"""
Native PyQt6 UI for Study Tracker calendar.
Replaces the HTML/JS webview with pure Qt widgets.
Features: calendar view, goal tracking, completion status, friend management.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Optional

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QGridLayout, QScrollArea, QFrame, QColor, QFont, Qt, QMessageBox,
    QThread, pyqtSignal, QTabWidget, QLineEdit, QColorDialog, QSpinBox,
    QFormLayout, QInputDialog
)

from . import sync, tracker


class SyncWorker(QThread):
    """Background worker for git sync to prevent UI freezing."""
    finished = pyqtSignal(bool, str)

    def run(self):
        ok, msg = sync.push_my_data()
        self.finished.emit(ok, msg)


class GoalManager:
    """Manage study goals and completion status."""

    def __init__(self):
        self.goals = self._load_goals()

    def _load_goals(self) -> dict:
        """Load goals from config."""
        cfg = mw.addonManager.getConfig(__name__) or {}
        return cfg.get("goals", {"daily": 10, "weekly": 50})

    def save_goals(self, daily: int, weekly: int):
        """Save goals to config."""
        cfg = mw.addonManager.getConfig(__name__) or {}
        cfg["goals"] = {"daily": daily, "weekly": weekly}
        mw.addonManager.setConfig(__name__, cfg)
        self.goals = cfg.get("goals", {})

    def get_completion_status(self, date_obj: datetime, friends_data: list) -> str:
        """
        Get status emoji for a date:
        ✓ = completed (all members studied)
        ◐ = almost (70%+ studied)
        ◑ = half (50%+ studied)
        ✗ = not completed (less than 50%)
        """
        date_str = date_obj.strftime("%Y-%m-%d")
        if not friends_data:
            return "·"
        
        studied = sum(1 for f in friends_data if date_str in f.get("reviews", {}) and f["reviews"][date_str] > 0)
        pct = (studied / len(friends_data)) * 100 if friends_data else 0
        
        if pct >= 100:
            return "✓"
        elif pct >= 70:
            return "◐"
        elif pct >= 50:
            return "◑"
        else:
            return "✗"

    def get_status_color(self, status: str) -> str:
        """Get color for status badge."""
        colors = {
            "✓": "#3ecf8e",  # green - completed
            "◐": "#f5a623",  # amber - almost done
            "◑": "#ffd700",  # gold - half done
            "✗": "#f87171",  # red - not done
            "·": "#cccccc",  # gray - empty
        }
        return colors.get(status, "#888888")


class DayCell(QFrame):
    """A single day cell in the calendar grid."""

    def __init__(self, date_obj: Optional[datetime], friends_data: list, parent=None, goal_manager=None):
        super().__init__(parent)
        self.date_obj = date_obj
        self.friends_data = friends_data
        self.goal_manager = goal_manager
        self.selected = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 12px;
                background: #ffffff;
            }
            QFrame:hover {
                border-color: rgba(0,0,0,0.15);
                background: #f5f5f5;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 7)
        layout.setSpacing(4)

        if date_obj:
            # Status badge + Date number
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(4)
            
            if self.goal_manager:
                status = self.goal_manager.get_completion_status(date_obj, friends_data)
                status_color = self.goal_manager.get_status_color(status)
                status_label = QLabel(status)
                status_label.setStyleSheet(f"""
                    color: {status_color};
                    font-size: 11px;
                    font-weight: 700;
                """)
                status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                status_label.setFixedSize(14, 14)
                header_layout.addWidget(status_label)
            
            day_label = QLabel(str(date_obj.day))
            day_label.setStyleSheet("""
                color: #666666;
                font-size: 12px;
                font-weight: 500;
                font-family: 'Courier New', monospace;
            """)
            header_layout.addWidget(day_label)
            header_layout.addStretch()
            layout.addLayout(header_layout)

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
                    background: linear-gradient(to right, #7c6af7 {progress_pct}%, #e8e8e8 {progress_pct}%);
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
                    border: 1px solid #7c6af7;
                    border-radius: 12px;
                    background: #f5f5f5;
                    box-shadow: 0 0 0 1px #7c6af7;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid rgba(0,0,0,0.1);
                    border-radius: 12px;
                    background: #ffffff;
                }
                QFrame:hover {
                    border-color: rgba(0,0,0,0.15);
                    background: #f5f5f5;
                }
            """)


class CalendarPanel(QWidget):
    """Left panel with calendar grid."""

    cell_clicked = pyqtSignal(object)

    def __init__(self, friends_data: list, parent=None, goal_manager=None):
        super().__init__(parent)
        self.friends_data = friends_data
        self.goal_manager = goal_manager
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

        # Legend for status badges
        legend_layout = QHBoxLayout()
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(12)
        legend_label = QLabel("Status:")
        legend_label.setStyleSheet("font-size: 11px; color: #888888; font-weight: 500;")
        legend_layout.addWidget(legend_label)
        
        for status, label in [("✓", "All"), ("◐", "Most"), ("◑", "Half"), ("✗", "Few")]:
            color = goal_manager.get_status_color(status) if goal_manager else "#888888"
            badge = QLabel(status)
            badge.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 700;")
            badge.setFixedSize(14, 14)
            legend_layout.addWidget(badge)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 10px; color: #999999;")
            legend_layout.addWidget(lbl)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        # Calendar grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6)

        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            hdr = QLabel(day)
            hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hdr.setStyleSheet("""
                color: #888888;
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
        for i in reversed(range(1, self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        self.month_label.setText(self.current_date.strftime("%B %Y").capitalize())

        first_day = self.current_date.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        start_weekday = first_day.weekday()
        row = 1
        col = start_weekday

        for i in range(start_weekday):
            cell = DayCell(None, self.friends_data, self, self.goal_manager)
            self.grid_layout.addWidget(cell, row, i)

        for day in range(1, last_day.day + 1):
            date_obj = self.current_date.replace(day=day)
            cell = DayCell(date_obj, self.friends_data, self, self.goal_manager)
            cell.mousePressEvent = lambda ev, d=date_obj: self._on_cell_clicked(d)
            self.grid_layout.addWidget(cell, row, col)

            col += 1
            if col == 7:
                col = 0
                row += 1

        while col < 7:
            cell = DayCell(None, self.friends_data, self, self.goal_manager)
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
        self.empty_label.setStyleSheet("color: #999999; font-size: 13px;")

        layout.addSpacing(24)
        layout.addWidget(self.empty_label)
        layout.addStretch()

        self.setMinimumWidth(280)
        self.setStyleSheet("""
            QWidget {
                border-left: 1px solid rgba(0,0,0,0.1);
                background: #fafafa;
            }
        """)

    def show_date_details(self, date_obj: datetime, friends_data: list):
        self.selected_date = date_obj

        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        layout = self.layout()
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setSpacing(0)

        date_str = date_obj.strftime("%Y-%m-%d")
        weekday_str = date_obj.strftime("%A")

        date_label = QLabel(date_str)
        date_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #000000;")
        layout.addWidget(date_label)

        weekday_label = QLabel(weekday_str)
        weekday_label.setStyleSheet("font-size: 11px; color: #888888; margin-top: 2px;")
        layout.addWidget(weekday_label)

        layout.addSpacing(12)

        total_friends = len(friends_data)
        studied_today = sum(1 for f in friends_data if date_str in f.get("reviews", {}) and f["reviews"][date_str] > 0)

        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(8)

        stat1 = QFrame()
        stat1.setStyleSheet("background: #f0f0f0; border-radius: 8px; padding: 8px 10px;")
        stat1_layout = QVBoxLayout(stat1)
        stat1_layout.setContentsMargins(8, 8, 8, 8)
        stat1_val = QLabel(str(studied_today))
        stat1_val.setStyleSheet("font-size: 18px; font-weight: 600; color: #000000; font-family: 'Courier New';")
        stat1_key = QLabel("STUDIED")
        stat1_key.setStyleSheet("font-size: 10px; color: #888888; margin-top: 2px; text-transform: uppercase;")
        stat1_layout.addWidget(stat1_val)
        stat1_layout.addWidget(stat1_key)
        stats_layout.addWidget(stat1)

        stat2 = QFrame()
        stat2.setStyleSheet("background: #f0f0f0; border-radius: 8px; padding: 8px 10px;")
        stat2_layout = QVBoxLayout(stat2)
        stat2_layout.setContentsMargins(8, 8, 8, 8)
        stat2_val = QLabel(str(total_friends))
        stat2_val.setStyleSheet("font-size: 18px; font-weight: 600; color: #000000; font-family: 'Courier New';")
        stat2_key = QLabel("GROUP")
        stat2_key.setStyleSheet("font-size: 10px; color: #888888; margin-top: 2px; text-transform: uppercase;")
        stat2_layout.addWidget(stat2_val)
        stat2_layout.addWidget(stat2_key)
        stats_layout.addWidget(stat2)

        layout.addLayout(stats_layout)
        layout.addSpacing(12)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(0,0,0,0.1);")
        layout.addWidget(divider)

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
        row_widget = QWidget()
        row_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-bottom: 1px solid rgba(0,0,0,0.08);
                padding: 10px 0;
            }
            QWidget:hover { background: #f5f5f5; }
        """)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 10, 0, 10)
        row_layout.setSpacing(10)

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

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(friend.get("name", "Unknown"))
        name_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #000000;")
        info_layout.addWidget(name_label)

        reviews = friend.get("reviews", {}).get(date_str, 0)
        count_label = QLabel(f"{reviews} cards" if reviews > 0 else "—")
        count_label.setStyleSheet("font-size: 11px; color: #888888; font-family: 'Courier New';")
        info_layout.addWidget(count_label)

        row_layout.addLayout(info_layout)

        badge_text = "Done" if reviews > 0 else "Miss"
        badge_color = "background: rgba(62,207,142,0.15); color: #3ecf8e;" if reviews > 0 else "background: rgba(0,0,0,0.05); color: #999999;"
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


class SettingsTab(QWidget):
    """Settings tab for goals, friends, and data management."""

    def __init__(self, parent=None, goal_manager=None):
        super().__init__(parent)
        self.goal_manager = goal_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Goals section
        goals_frame = QFrame()
        goals_frame.setStyleSheet("background: #f5f5f5; border-radius: 8px; padding: 16px;")
        goals_layout = QVBoxLayout(goals_frame)

        goals_title = QLabel("📊 Study Goals")
        goals_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #000000;")
        goals_layout.addWidget(goals_title)

        goals_form = QFormLayout()
        goals_form.setSpacing(8)

        self.daily_spin = QSpinBox()
        self.daily_spin.setMinimum(1)
        self.daily_spin.setMaximum(500)
        self.daily_spin.setValue(self.goal_manager.goals.get("daily", 10))
        self.daily_spin.setStyleSheet("padding: 6px;")
        goals_form.addRow("Daily goal (cards):", self.daily_spin)

        self.weekly_spin = QSpinBox()
        self.weekly_spin.setMinimum(1)
        self.weekly_spin.setMaximum(5000)
        self.weekly_spin.setValue(self.goal_manager.goals.get("weekly", 50))
        self.weekly_spin.setStyleSheet("padding: 6px;")
        goals_form.addRow("Weekly goal (cards):", self.weekly_spin)

        goals_save_btn = QPushButton("💾 Save Goals")
        goals_save_btn.setStyleSheet("""
            QPushButton {
                background: #7c6af7;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover { opacity: 0.85; }
        """)
        goals_save_btn.clicked.connect(self._save_goals)
        goals_form.addRow("", goals_save_btn)

        goals_layout.addLayout(goals_form)
        layout.addWidget(goals_frame)

        # Data management section
        data_frame = QFrame()
        data_frame.setStyleSheet("background: #f5f5f5; border-radius: 8px; padding: 16px;")
        data_layout = QVBoxLayout(data_frame)

        data_title = QLabel("🗑️ Data Management")
        data_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #000000;")
        data_layout.addWidget(data_title)

        clear_btn = QPushButton("⚠️ Clear All Study Data")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #f87171;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                padding: 10px 16px;
            }
            QPushButton:hover { opacity: 0.85; }
        """)
        clear_btn.clicked.connect(self._clear_data)
        data_layout.addWidget(clear_btn)

        layout.addWidget(data_frame)

        # About section
        about_frame = QFrame()
        about_frame.setStyleSheet("background: #f5f5f5; border-radius: 8px; padding: 16px;")
        about_layout = QVBoxLayout(about_frame)

        about_title = QLabel("ℹ️ Status")
        about_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #000000;")
        about_layout.addWidget(about_title)

        cfg = mw.addonManager.getConfig(__name__) or {}
        self.info_label = QLabel(f"User: {cfg.get('my_name', 'Unknown')}\nColor: {cfg.get('my_color', 'N/A')}")
        self.info_label.setStyleSheet("font-size: 12px; color: #666666; font-family: 'Courier New';")
        about_layout.addWidget(self.info_label)

        layout.addWidget(about_frame)
        layout.addStretch()

    def _save_goals(self):
        daily = self.daily_spin.value()
        weekly = self.weekly_spin.value()
        self.goal_manager.save_goals(daily, weekly)
        QMessageBox.information(self, "Study Tracker", "✓ Goals saved!")

    def _clear_data(self):
        reply = QMessageBox.warning(
            self, "Study Tracker",
            "⚠️ This will clear ALL study data from Anki revlog.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if mw.col:
                    mw.col.db.execute("DELETE FROM revlog")
                    mw.reset()
                    QMessageBox.information(self, "Study Tracker", "✓ All data cleared!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear data:\n{str(e)}")


class GoalsTab(QWidget):
    """Tab for viewing and managing group goals."""

    def __init__(self, parent=None, friends_data: list = None, goal_manager=None):
        super().__init__(parent)
        self.friends_data = friends_data or []
        self.goal_manager = goal_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Goals display
        title = QLabel("📈 Group Study Goals")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #000000;")
        layout.addWidget(title)

        if goal_manager:
            daily_goal = goal_manager.goals.get("daily", 10)
            weekly_goal = goal_manager.goals.get("weekly", 50)

            goals_info = QLabel(
                f"Daily Goal: {daily_goal} cards\n"
                f"Weekly Goal: {weekly_goal} cards\n\n"
                f"Tracked Members: {len(self.friends_data)}"
            )
            goals_info.setStyleSheet("""
                font-size: 13px;
                color: #333333;
                background: #f0f0f0;
                border-radius: 8px;
                padding: 16px;
            """)
            layout.addWidget(goals_info)

        # Member list
        members_title = QLabel("👥 Members")
        members_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #000000; margin-top: 12px;")
        layout.addWidget(members_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(6)

        for friend in self.friends_data:
            member_row = QFrame()
            member_row.setStyleSheet("background: #f5f5f5; border-radius: 6px; padding: 10px;")
            member_layout = QHBoxLayout(member_row)

            avatar = QLabel(friend.get("name", "?")[0].upper())
            avatar.setStyleSheet(f"""
                background: {friend.get("color", "#378ADD")};
                color: white;
                border-radius: 6px;
                width: 28px;
                height: 28px;
                font-weight: bold;
                text-align: center;
                line-height: 28px;
            """)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            member_layout.addWidget(avatar)

            name = QLabel(friend.get("name", "Unknown"))
            name.setStyleSheet("font-size: 13px; font-weight: 500; color: #000000;")
            member_layout.addWidget(name)

            member_layout.addStretch()
            scroll_layout.addWidget(member_row)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)


class TrackerWindowQt(QDialog):
    """Main tracker window with native Qt UI."""

    def __init__(self):
        super().__init__(mw)
        self.setWindowTitle("Study Tracker – Group Calendar")
        self.resize(1400, 720)

        self.friends_data: list = []
        self.sync_worker: Optional[SyncWorker] = None
        self.goal_manager = GoalManager()

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar
        topbar = QWidget()
        topbar.setStyleSheet("background: #ffffff; border-bottom: 1px solid rgba(0,0,0,0.1);")
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
        title_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #000000;")
        title_layout.addWidget(title_label)
        subtitle_label = QLabel("group.json")
        subtitle_label.setStyleSheet("font-size: 12px; color: #888888; font-family: 'Courier New';")
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
        legend_bar.setStyleSheet("background: #fafafa; border-bottom: 1px solid rgba(0,0,0,0.08); padding: 12px 28px;")
        legend_layout = QHBoxLayout(legend_bar)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(6)
        legend_label = QLabel("MEMBERS")
        legend_label.setStyleSheet("font-size: 11px; color: #888888; text-transform: uppercase;")
        legend_layout.addWidget(legend_label)
        legend_layout.addStretch()
        main_layout.addWidget(legend_bar)

        # Content area with tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #fafafa;
                border: none;
                padding: 8px 16px;
                margin-right: 2px;
                color: #666666;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #7c6af7;
                color: #000000;
            }
        """)

        # Calendar tab
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.calendar_panel = CalendarPanel([], self, self.goal_manager)
        self.calendar_panel.cell_clicked.connect(self._on_cell_clicked)
        content_layout.addWidget(self.calendar_panel)

        self.detail_panel = DetailPanel(self)
        content_layout.addWidget(self.detail_panel)

        self.tabs.addTab(content, "📅 Calendar")

        # Goals tab
        self.goals_tab = GoalsTab(self, [], self.goal_manager)
        self.tabs.addTab(self.goals_tab, "📈 Goals")

        # Settings tab
        self.settings_tab = SettingsTab(self, self.goal_manager)
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")

        main_layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("""
            QLabel {
                background: #fafafa;
                border-top: 1px solid rgba(0,0,0,0.08);
                padding: 10px 28px;
                font-size: 11px;
                color: #888888;
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

        names_in_repo = {f.get("name", "") for f in self.friends_data}
        if my_name not in names_in_repo:
            self.friends_data.append({
                "name": my_name,
                "color": my_color,
                "reviews": tracker.get_my_reviews(),
                "last_updated": "",
            })

        self.calendar_panel.set_friends_data(self.friends_data)
        self.goals_tab.friends_data = self.friends_data
        self.status_bar.setText(f"Ready – {len(self.friends_data)} members")

    def _on_cell_clicked(self, date_obj: datetime):
        self.detail_panel.show_date_details(date_obj, self.friends_data)

    def _on_sync_clicked(self):
        self.sync_btn.setEnabled(False)
        self.status_bar.setText("Syncing...")

        self.sync_worker = SyncWorker()
        self.sync_worker.finished.connect(self._on_sync_done)
        self.sync_worker.start()

    def _on_sync_done(self, ok: bool, msg: str):
        self.sync_btn.setEnabled(True)
        self.status_bar.setText(f"Synced: {msg}" if ok else f"Sync failed: {msg}")

        if ok:
            self._load_data()
            QMessageBox.information(self, "Study Tracker", msg)
        else:
            QMessageBox.warning(self, "Study Tracker", f"Sync failed:\n{msg}")

    def refresh(self):
        self._load_data()


def show_tracker_window():
    """Open the tracker window."""
    win = TrackerWindowQt()
    win.exec()
