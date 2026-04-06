"""
Simplified Study Tracker UI - Just calendar view + settings button.
"""

import json
import time
import os
from datetime import datetime, timedelta
from typing import Optional

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QGridLayout, QScrollArea, QFrame, Qt, QMessageBox,
    QThread, pyqtSignal, QSpinBox, QFormLayout, QLineEdit,
    QColorDialog, QTabWidget, QListWidget, QListWidgetItem, QColor
)

from . import sync, tracker


def _save_config(cfg: dict):
    """Save config directly to config.json file."""
    addon_dir = os.path.dirname(__file__)
    config_path = os.path.join(addon_dir, "config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")


def _load_config() -> dict:
    """Load config from config.json file."""
    addon_dir = os.path.dirname(__file__)
    config_path = os.path.join(addon_dir, "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
    return {}


class SyncWorker(QThread):
    """Background worker for git sync."""
    finished = pyqtSignal(bool, str)

    def run(self):
        ok, msg = sync.push_my_data()
        self.finished.emit(ok, msg)


class GoalManager:
    """Manage study goals (shared across all users)."""

    def __init__(self):
        self.goals = self._load_goals()

    def _load_goals(self) -> dict:
        """Load goals from shared goals.json file."""
        addon_dir = os.path.dirname(__file__)
        goals_path = os.path.join(addon_dir, "goals.json")
        try:
            if os.path.exists(goals_path):
                with open(goals_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading goals: {e}")
        return {"daily": 10, "weekly": 50}

    def save_goals(self, daily: int, weekly: int):
        """Save goals to shared goals.json file."""
        addon_dir = os.path.dirname(__file__)
        goals_path = os.path.join(addon_dir, "goals.json")
        try:
            with open(goals_path, "w") as f:
                json.dump({"daily": daily, "weekly": weekly}, f, indent=2)
            self.goals = {"daily": daily, "weekly": weekly}
        except Exception as e:
            print(f"Error saving goals: {e}")

    def get_status(self, date_obj: datetime, friends_data: list) -> str:
        """Get status based on daily goal completion.
        ✓ = completed goal | ✗ = not completed | · = no data
        """
        date_str = date_obj.strftime("%Y-%m-%d")
        daily_goal = self.goals.get("daily", 10)
        
        completed = 0
        has_data = False
        
        for f in friends_data:
            reviews = f.get("reviews", {})
            if date_str in reviews and reviews[date_str] > 0:
                has_data = True
                if reviews[date_str] >= daily_goal:
                    completed += 1
        
        if not has_data:
            return "·"
        
        # All completed
        if completed == len(friends_data):
            return "✓"
        # Some completed
        elif completed > 0:
            return "◐"
        else:
            return "✗"

    def get_color(self, status: str) -> str:
        return {
            "✓": "#3ecf8e",  # green - all done
            "◐": "#f5a623",  # amber - some done
            "✗": "#f87171",  # red - none done
            "·": "#cccccc",  # gray - no data
        }.get(status, "#888888")



class SetupWizard(QDialog):
    """First time setup wizard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Study Tracker - First Time Setup")
        self.resize(450, 280)
        self._color = "#378ADD"

        l = QVBoxLayout(self)
        l.setContentsMargins(30, 30, 30, 30)
        l.setSpacing(16)

        # Title
        title = QLabel("👋 Welcome to Study Tracker!")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #000000;")
        l.addWidget(title)

        # Description
        desc = QLabel("Let's set up your profile. You can change these anytime in Settings.")
        desc.setStyleSheet("font-size: 12px; color: #888888;")
        desc.setWordWrap(True)
        l.addWidget(desc)

        l.addSpacing(8)

        # Form
        f = QFormLayout()
        f.setSpacing(12)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Your name")
        self.name.setText("Ban")
        f.addRow("Name:", self.name)

        color_layout = QHBoxLayout()
        self.color_btn = QPushButton("🎨 #378ADD")
        self.color_btn.setMaximumWidth(120)
        self.color_btn.setStyleSheet("background: #378ADD; color: white; border: none; border-radius: 6px; padding: 6px;")
        self.color_btn.clicked.connect(self._pick_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        f.addRow("Color:", color_layout)

        l.addLayout(f)
        l.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        skip = QPushButton("⏭️ Skip")
        skip.setStyleSheet("background: #f0f0f0; border: none; border-radius: 6px; padding: 8px 16px;")
        skip.clicked.connect(self._save_default)
        btn_layout.addWidget(skip)

        save = QPushButton("✓ Save & Continue")
        save.setStyleSheet("""
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
        save.clicked.connect(self._save)
        btn_layout.addWidget(save)
        l.addLayout(btn_layout)

    def _pick_color(self):
        initial_color = QColor(self._color)
        color = QColorDialog.getColor(initial=initial_color, parent=self)
        if color.isValid():
            self._color = color.name()
            self.color_btn.setText("🎨 " + self._color)
            self.color_btn.setStyleSheet(f"background: {self._color}; color: white; border: none; border-radius: 6px; padding: 6px;")

    def _save_default(self):
        cfg = {
            "my_name": "Ban",
            "my_color": "#378ADD"
        }
        _save_config(cfg)
        self.accept()

    def _save(self):
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name cannot be empty!")
            return

        cfg = {
            "my_name": name,
            "my_color": self._color
        }
        _save_config(cfg)
        self.accept()


class DayCell(QFrame):
    """Calendar day cell."""

    def __init__(self, date_obj: Optional[datetime], friends_data: list, parent=None, goal_manager=None):
        super().__init__(parent)
        self.date_obj = date_obj
        self.friends_data = friends_data
        self.goal_manager = goal_manager

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
            header = QHBoxLayout()
            header.setContentsMargins(0, 0, 0, 0)
            header.setSpacing(4)
            
            if goal_manager:
                status = goal_manager.get_status(date_obj, friends_data)
                color = goal_manager.get_color(status)
                badge = QLabel(status)
                badge.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 700;")
                badge.setFixedSize(14, 14)
                header.addWidget(badge)
            
            day = QLabel(str(date_obj.day))
            day.setStyleSheet("color: #666666; font-size: 12px; font-weight: 500; font-family: 'Courier New', monospace;")
            header.addWidget(day)
            header.addStretch()
            layout.addLayout(header)

            avatars = QHBoxLayout()
            avatars.setSpacing(3)
            avatars.setContentsMargins(0, 0, 0, 0)

            date_str = date_obj.strftime("%Y-%m-%d")
            for friend in friends_data:
                if date_str in friend.get("reviews", {}) and friend["reviews"][date_str] > 0:
                    av = QLabel(friend["name"][0].upper() if friend.get("name") else "?")
                    av.setStyleSheet(f"""
                        background: {friend.get("color", "#378ADD")};
                        color: white;
                        border-radius: 11px;
                        width: 22px;
                        height: 22px;
                        font-weight: bold;
                        font-size: 9px;
                        text-align: center;
                        line-height: 22px;
                    """)
                    av.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    avatars.addWidget(av)

            avatars.addStretch()
            layout.addLayout(avatars)

            layout.addSpacing(2)
            total = sum(1 for f in friends_data if date_str in f.get("reviews", {}) and f["reviews"][date_str] > 0)
            if total > 0 and friends_data:
                pct = (total / len(friends_data)) * 100
                bar = QLabel()
                bar.setStyleSheet(f"background: linear-gradient(to right, #7c6af7 {pct}%, #e8e8e8 {pct}%); height: 2px; border-radius: 2px;")
                layout.addWidget(bar)

            layout.addStretch()
        else:
            layout.addStretch()

        self.setMinimumHeight(88)


class CalendarPanel(QWidget):
    """Calendar grid."""

    cell_clicked = pyqtSignal(object)

    def __init__(self, friends_data: list, parent=None, goal_manager=None):
        super().__init__(parent)
        self.friends_data = friends_data
        self.goal_manager = goal_manager
        self.current_date = datetime.now()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        nav = QHBoxLayout()
        prev_btn = QPushButton("‹")
        prev_btn.setMaximumWidth(36)
        prev_btn.setMaximumHeight(36)
        prev_btn.clicked.connect(self._prev)
        nav.addWidget(prev_btn)

        next_btn = QPushButton("›")
        next_btn.setMaximumWidth(36)
        next_btn.setMaximumHeight(36)
        next_btn.clicked.connect(self._next)
        nav.addWidget(next_btn)

        self.month = QLabel()
        self.month.setStyleSheet("font-size: 22px; font-weight: 600;")
        self.month.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self.month)

        nav.addStretch()

        today = QPushButton("Today")
        today.setMaximumHeight(36)
        today.clicked.connect(self._today)
        nav.addWidget(today)

        layout.addLayout(nav)

        # Legend
        legend = QHBoxLayout()
        legend.setContentsMargins(0, 0, 0, 0)
        legend.setSpacing(12)
        lbl = QLabel("Status:")
        lbl.setStyleSheet("font-size: 11px; color: #888888; font-weight: 500;")
        legend.addWidget(lbl)
        
        for s, l in [("✓", "All done"), ("◐", "Some done"), ("✗", "None done")]:
            c = goal_manager.get_color(s) if goal_manager else "#888888"
            b = QLabel(s)
            b.setStyleSheet(f"color: {c}; font-size: 10px; font-weight: 700;")
            b.setFixedSize(14, 14)
            legend.addWidget(b)
            n = QLabel(l)
            n.setStyleSheet("font-size: 10px; color: #999999;")
            legend.addWidget(n)
        
        legend.addStretch()
        layout.addLayout(legend)

        self.grid = QGridLayout()
        self.grid.setSpacing(6)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            hdr = QLabel(day)
            hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hdr.setStyleSheet("color: #888888; font-size: 11px; font-weight: 500; text-transform: uppercase;")
            self.grid.addWidget(hdr, 0, i)

        layout.addLayout(self.grid)
        layout.addStretch()

        self._update()

    def _update(self):
        for i in reversed(range(1, self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

        self.month.setText(self.current_date.strftime("%B %Y").capitalize())

        first = self.current_date.replace(day=1)
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        sw = first.weekday()
        row, col = 1, sw

        for i in range(sw):
            self.grid.addWidget(DayCell(None, self.friends_data, self, self.goal_manager), row, i)

        for day in range(1, last.day + 1):
            d = self.current_date.replace(day=day)
            c = DayCell(d, self.friends_data, self, self.goal_manager)
            c.mousePressEvent = lambda e, x=d: self.cell_clicked.emit(x)
            self.grid.addWidget(c, row, col)
            col += 1
            if col == 7:
                col, row = 0, row + 1

        while col < 7:
            self.grid.addWidget(DayCell(None, self.friends_data, self, self.goal_manager), row, col)
            col += 1

    def _prev(self):
        self.current_date = (self.current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        self._update()

    def _next(self):
        self.current_date = (self.current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        self._update()

    def _today(self):
        self.current_date = datetime.now()
        self._update()

    def set_data(self, friends_data: list):
        self.friends_data = friends_data
        self._update()


class DetailPanel(QWidget):
    """Detail panel."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        self.empty = QLabel("Select a day")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setStyleSheet("color: #999999; font-size: 13px;")

        layout.addSpacing(24)
        layout.addWidget(self.empty)
        layout.addStretch()

        self.setMinimumWidth(280)
        self.setStyleSheet("""
            QWidget {
                border-left: 1px solid rgba(0,0,0,0.1);
                background: #fafafa;
            }
        """)

    def show_date(self, date_obj: datetime, friends_data: list):
        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        layout = self.layout()
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setSpacing(0)

        d_str = date_obj.strftime("%Y-%m-%d")
        w_str = date_obj.strftime("%A")

        date_lbl = QLabel(d_str)
        date_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #000000;")
        layout.addWidget(date_lbl)

        week_lbl = QLabel(w_str)
        week_lbl.setStyleSheet("font-size: 11px; color: #888888; margin-top: 2px;")
        layout.addWidget(week_lbl)

        layout.addSpacing(12)

        total = len(friends_data)
        studied = sum(1 for f in friends_data if d_str in f.get("reviews", {}) and f["reviews"][d_str] > 0)

        stats = QHBoxLayout()
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(8)

        s1 = QFrame()
        s1.setStyleSheet("background: #f0f0f0; border-radius: 8px; padding: 8px 10px;")
        s1l = QVBoxLayout(s1)
        s1l.setContentsMargins(8, 8, 8, 8)
        s1v = QLabel(str(studied))
        s1v.setStyleSheet("font-size: 18px; font-weight: 600; color: #000000; font-family: 'Courier New';")
        s1k = QLabel("STUDIED")
        s1k.setStyleSheet("font-size: 10px; color: #888888; margin-top: 2px; text-transform: uppercase;")
        s1l.addWidget(s1v)
        s1l.addWidget(s1k)
        stats.addWidget(s1)

        s2 = QFrame()
        s2.setStyleSheet("background: #f0f0f0; border-radius: 8px; padding: 8px 10px;")
        s2l = QVBoxLayout(s2)
        s2l.setContentsMargins(8, 8, 8, 8)
        s2v = QLabel(str(total))
        s2v.setStyleSheet("font-size: 18px; font-weight: 600; color: #000000; font-family: 'Courier New';")
        s2k = QLabel("TOTAL")
        s2k.setStyleSheet("font-size: 10px; color: #888888; margin-top: 2px; text-transform: uppercase;")
        s2l.addWidget(s2v)
        s2l.addWidget(s2k)
        stats.addWidget(s2)

        layout.addLayout(stats)
        layout.addSpacing(12)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: rgba(0,0,0,0.1);")
        layout.addWidget(div)

        layout.addSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        for f in friends_data:
            row = QWidget()
            row.setStyleSheet("""
                QWidget {
                    background: transparent;
                    border-bottom: 1px solid rgba(0,0,0,0.08);
                    padding: 10px 0;
                }
                QWidget:hover { background: #f5f5f5; }
            """)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 10, 0, 10)
            rl.setSpacing(10)

            av = QLabel(f.get("name", "?")[0].upper())
            av.setStyleSheet(f"""
                background: {f.get("color", "#378ADD")};
                color: white;
                border-radius: 11px;
                width: 28px;
                height: 28px;
                font-weight: bold;
                font-size: 11px;
                text-align: center;
                line-height: 28px;
            """)
            av.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rl.addWidget(av)

            il = QVBoxLayout()
            il.setContentsMargins(0, 0, 0, 0)
            il.setSpacing(2)

            nm = QLabel(f.get("name", "Unknown"))
            nm.setStyleSheet("font-size: 13px; font-weight: 500; color: #000000;")
            il.addWidget(nm)

            cnt = f.get("reviews", {}).get(d_str, 0)
            ct = QLabel(f"{cnt} cards" if cnt > 0 else "—")
            ct.setStyleSheet("font-size: 11px; color: #888888; font-family: 'Courier New';")
            il.addWidget(ct)

            rl.addLayout(il)

            bg = "Done" if cnt > 0 else "Miss"
            bc = "background: rgba(62,207,142,0.15); color: #3ecf8e;" if cnt > 0 else "background: rgba(0,0,0,0.05); color: #999999;"
            bdg = QLabel(bg)
            bdg.setStyleSheet(f"font-size: 10px; font-weight: 600; border-radius: 20px; padding: 3px 9px; text-transform: uppercase; {bc}")
            rl.addWidget(bdg)

            sl.addWidget(row)

        sl.addStretch()
        scroll.setWidget(sw)
        layout.addWidget(scroll)


class MainWindow(QDialog):
    """Main window - simplified."""

    def __init__(self):
        super().__init__(mw)
        self.setWindowTitle("Study Tracker")
        self.resize(1200, 700)

        # Check if config needs setup
        cfg = _load_config()
        if not cfg or not cfg.get("my_name") or not cfg.get("my_color"):
            wizard = SetupWizard(self)
            wizard.exec()

        self.friends_data: list = []
        self.sync_worker: Optional[SyncWorker] = None
        self.goal_manager = GoalManager()

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # Top bar
        top = QWidget()
        top.setStyleSheet("background: #ffffff; border-bottom: 1px solid rgba(0,0,0,0.1);")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(28, 18, 28, 18)
        tl.setSpacing(14)

        tl.addWidget(QLabel("📅"))

        tit = QVBoxLayout()
        tit.setContentsMargins(0, 0, 0, 0)
        tit.setSpacing(1)
        title = QLabel("Study Tracker")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #000000;")
        tit.addWidget(title)
        
        cfg = mw.addonManager.getConfig(__name__) or {}
        sub = QLabel(f"{cfg.get('my_name', 'Me')}")
        sub.setStyleSheet("font-size: 12px; color: #888888; font-family: 'Courier New';")
        tit.addWidget(sub)
        tl.addLayout(tit)

        tl.addStretch()

        self.sync_btn = QPushButton("↻ Sync")
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background: #7c6af7;
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                font-size: 13px;
                padding: 8px 14px;
            }
            QPushButton:hover { opacity: 0.85; }
        """)
        self.sync_btn.clicked.connect(self._sync)
        tl.addWidget(self.sync_btn)

        set_btn = QPushButton("⚙️")
        set_btn.setMaximumWidth(40)
        set_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                padding: 6px;
            }
            QPushButton:hover { background: #e0e0e0; }
        """)
        set_btn.clicked.connect(self._settings)
        tl.addWidget(set_btn)

        main.addWidget(top)

        # Calendar
        cont = QWidget()
        cl = QHBoxLayout(cont)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        self.cal = CalendarPanel([], self, self.goal_manager)
        self.cal.cell_clicked.connect(self._cell_click)
        cl.addWidget(self.cal)

        self.det = DetailPanel(self)
        cl.addWidget(self.det)

        main.addWidget(cont)

        # Status bar
        self.status = QLabel("Ready")
        self.status.setStyleSheet("""
            QLabel {
                background: #fafafa;
                border-top: 1px solid rgba(0,0,0,0.08);
                padding: 10px 28px;
                font-size: 11px;
                color: #888888;
                font-family: 'Courier New';
            }
        """)
        main.addWidget(self.status)

        self._load()

    def _load(self):
        self.friends_data = sync.pull_all_data()

        cfg = mw.addonManager.getConfig(__name__) or {}
        my_name = cfg.get("my_name", "Me").strip()
        my_color = cfg.get("my_color", "#378ADD")

        names = {f.get("name", "") for f in self.friends_data}
        if my_name not in names:
            self.friends_data.append({
                "name": my_name,
                "color": my_color,
                "reviews": tracker.get_my_reviews(),
                "last_updated": "",
            })

        self.cal.set_data(self.friends_data)
        self.status.setText(f"Ready – {len(self.friends_data)} members")

    def _cell_click(self, date_obj):
        self.det.show_date(date_obj, self.friends_data)

    def _settings(self):
        d = QDialog(self)
        d.setWindowTitle("Settings")
        d.resize(500, 450)
        
        l = QVBoxLayout(d)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""QTabBar::tab { padding: 8px 16px; }""")

        # TAB 1: User Profile
        upt = QWidget()
        upl = QVBoxLayout(upt)
        upl.setContentsMargins(20, 20, 20, 20)
        upl.setSpacing(12)

        cfg = mw.addonManager.getConfig(__name__) or {}
        title = QLabel("🧑 Your Profile")
        title.setStyleSheet("font-size: 13px; font-weight: 600; color: #000000;")
        upl.addWidget(title)

        uf = QFormLayout()
        uf.setSpacing(10)
        self.user_name = QLineEdit()
        self.user_name.setText(cfg.get("my_name", "Me"))
        self.user_name.setPlaceholderText("Your name")
        uf.addRow("Name:", self.user_name)

        self.user_color = QPushButton("🎨 " + cfg.get("my_color", "#378ADD"))
        self.user_color.setMaximumWidth(120)
        self.user_color.setStyleSheet(f"background: {cfg.get('my_color', '#378ADD')}; color: white; border: none; border-radius: 6px; padding: 6px;")
        self.user_color.setData = lambda role, val: setattr(self, '_color', val) if role == Qt.ItemDataRole.UserRole else None
        self.user_color.data = lambda role: getattr(self, '_color', cfg.get('my_color', '#378ADD')) if role == Qt.ItemDataRole.UserRole else None
        self._color = cfg.get("my_color", "#378ADD")
        self.user_color.clicked.connect(lambda: self._pick_color(self.user_color))
        uf.addRow("Color:", self.user_color)

        upl.addLayout(uf)
        upl.addStretch()
        tabs.addTab(upt, "🧑 Profile")

        # TAB 2: Friends
        frt = QWidget()
        frl = QVBoxLayout(frt)
        frl.setContentsMargins(20, 20, 20, 20)
        frl.setSpacing(12)

        friends_title = QLabel("👥 Friends")
        friends_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #000000;")
        frl.addWidget(friends_title)

        info = QLabel("Friends list from GitHub sync. Add friends via shared config on GitHub.")
        info.setStyleSheet("font-size: 11px; color: #888888; margin-bottom: 12px;")
        info.setWordWrap(True)
        frl.addWidget(info)

        self.friend_list = QListWidget()
        self.friend_list.setStyleSheet("""QListWidget { border: 1px solid #ddd; border-radius: 6px; }""")
        for f in self.friends_data:
            if f.get("name") != cfg.get("my_name", "Me"):
                item = QListWidgetItem(f"🟢 {f.get('name', '?')}")
                item.setData(Qt.ItemDataRole.UserRole, f.get("color", "#378ADD"))
                self.friend_list.addItem(item)
        frl.addWidget(self.friend_list)

        frl.addStretch()
        tabs.addTab(frt, "👥 Friends")

        # TAB 3: Data
        drt = QWidget()
        drl = QVBoxLayout(drt)
        drl.setContentsMargins(20, 20, 20, 20)
        drl.setSpacing(12)

        data_title = QLabel("🗑️ Data Management")
        data_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #000000;")
        drl.addWidget(data_title)

        danger_title = QLabel("Danger Zone")
        danger_title.setStyleSheet("font-size: 11px; color: #f87171; font-weight: 600; margin-top: 8px;")
        drl.addWidget(danger_title)

        clr = QPushButton("Clear All Study Data")
        clr.setStyleSheet("""
            QPushButton {
                background: #f87171;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                padding: 8px;
            }
            QPushButton:hover { opacity: 0.85; }
        """)
        clr.clicked.connect(lambda: self._clear(d))
        drl.addWidget(clr)

        drl.addStretch()
        tabs.addTab(drt, "🗑️ Data")

        l.addWidget(tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 20, 20, 20)
        btn_layout.setSpacing(12)

        sv = QPushButton("💾 Save")
        sv.setStyleSheet("""
            QPushButton {
                background: #7c6af7;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                padding: 10px 16px;
                min-width: 100px;
            }
            QPushButton:hover { opacity: 0.85; }
        """)
        sv.clicked.connect(lambda: self._save(self.user_name.text(), self._color, d))
        btn_layout.addStretch()
        btn_layout.addWidget(sv)
        l.addLayout(btn_layout)

        d.exec()

    def _save(self, name, color, d):
        if not name.strip():
            QMessageBox.warning(self, "Error", "Name cannot be empty!")
            return
        
        cfg = _load_config() or {}
        cfg["my_name"] = name.strip()
        cfg["my_color"] = color
        _save_config(cfg)
        d.close()
        
        # Update display
        self._load()
        QMessageBox.information(self, "Study Tracker", "✓ Saved!")

    def _clear(self, d):
        if QMessageBox.warning(self, "Study Tracker", "Delete ALL data?\n\nThis cannot be undone!", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Yes:
            try:
                if mw.col:
                    mw.col.db.execute("DELETE FROM revlog")
                    mw.reset()
                    d.close()
                    QMessageBox.information(self, "Study Tracker", "✓ Cleared!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed:\n{str(e)}")

    def _pick_color(self, btn):
        cfg = mw.addonManager.getConfig(__name__) or {}
        initial_color = QColor(cfg.get("my_color", "#378ADD"))
        color = QColorDialog.getColor(initial=initial_color, parent=self)
        if color.isValid():
            hex_color = color.name()
            btn.setText("🎨 " + hex_color)
            btn.setStyleSheet(f"background: {hex_color}; color: white; border: none; border-radius: 6px; padding: 6px;")
            self._color = hex_color

    def _sync(self):
        self.sync_btn.setEnabled(False)
        self.status.setText("Syncing...")

        self.sync_worker = SyncWorker()
        self.sync_worker.finished.connect(self._sync_done)
        self.sync_worker.start()

    def _sync_done(self, ok: bool, msg: str):
        self.sync_btn.setEnabled(True)
        self.status.setText(f"Synced: {msg}" if ok else f"Failed: {msg}")
        if ok:
            self._load()


def show_tracker_window():
    """Open the tracker window."""
    win = MainWindow()
    win.exec()
