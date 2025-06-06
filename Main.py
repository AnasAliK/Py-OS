import sys
import warnings
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

warnings.filterwarnings("ignore", category=DeprecationWarning)
import os
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QMenuBar,
    QAction,
    QFileDialog,
    QMessageBox,
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QSizePolicy,
    QToolButton,
    QGridLayout, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QSize, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QBrush, QLinearGradient, QColor, QFontDatabase, QFont, QPainter, \
    QCursor
from datetime import datetime
import time
import random
from threading import Thread
from enum import Enum
from datetime import datetime


# The scheduler implements a priority-based Round-Robin algorithm where:
# - Higher priority processes get more CPU time
# - Only 3 processes can run simultaneously
# - Processes randomly switch between states to simulate real system behavior

# memory management
class MemoryPage:
    def __init__(self):
        self.is_used = False
        self.process_id = None
        self.last_used = time.time()

class MemoryManager:
    def __init__(self, total_pages=100):
        self.pages = [MemoryPage() for _ in range(total_pages)]
        self.page_faults = 0

    def allocate_page(self, pid):
        for page in self.pages:
            if not page.is_used:
                page.is_used = True
                page.process_id = pid
                page.last_used = time.time()
                return True
        self.page_faults += 1
        return False

    def free_pages(self, pid):
        for page in self.pages:
            if page.process_id == pid:
                page.is_used = False
                page.process_id = None

class ProcessMemory:
    def __init__(self, pid):
        self.pid = pid
        self.page_count = 0

    def allocate(self, memory_manager, pages_needed):
        allocated = 0
        for _ in range(pages_needed):
            if memory_manager.allocate_page(self.pid):
                allocated += 1
        self.page_count += allocated
        return allocated

    def free(self, memory_manager):
        memory_manager.free_pages(self.pid)
        self.page_count = 0  # Reset page_count when freed


class ProcessState(Enum):
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    BLOCKED = "Blocked"
    TERMINATED = "Terminated"


class DummyProcess:
    def __init__(self, pid, name, priority, memory_manager):
        self.pid = pid
        self.name = name
        self.priority = priority
        self.state = ProcessState.READY
        self.cpu_usage = 0
        self.start_time = time.time()
        self.last_state_change = time.time()
        self.thread = None
        self.is_running = True
        self.status = ""
        # Memory allocation based on priority
        self.memory = ProcessMemory(pid)
        pages_needed = priority * 2
        self.memory.allocate(memory_manager, pages_needed)
        self.memory_manager = memory_manager


    def run(self):
        while self.is_running:
            if self.state == ProcessState.RUNNING:
                # Simulate CPU usage between 1-100%
                self.cpu_usage = random.randint(1, 100)

                # Randomly change state
                if random.random() < 0.1:  # 10% chance to change state
                    new_state = random.choice([
                        ProcessState.WAITING,
                        ProcessState.BLOCKED,
                        ProcessState.READY
                    ])
                    self.change_state(new_state)

            elif self.state == ProcessState.READY:
                self.cpu_usage = 0
                if random.random() < 0.3:  # 30% chance to start running
                    self.change_state(ProcessState.RUNNING)

            elif self.state in [ProcessState.WAITING, ProcessState.BLOCKED]:
                self.cpu_usage = 0
                if random.random() < 0.2:  # 20% chance to become ready
                    self.change_state(ProcessState.READY)

            time.sleep(1)  # Update every second

    def change_state(self, new_state):
        self.state = new_state
        self.last_state_change = time.time()

    def start(self):
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        self.state = ProcessState.TERMINATED

_DUMMY_PROCESSES_CREATED = False

class ProcessScheduler:
    def __init__(self):
        self.process_manager = ProcessManager()
        self.memory_manager = MemoryManager()
        self.current_pid = ProcessManager._next_pid  # Sync PID counter
        self._dummy_processes_created = False
        self.create_dummy_processes()

        self.scheduler_thread = Thread(target=self.schedule_processes, daemon=True)
        self.scheduler_thread.start()



    def create_dummy_processes(self):
        global _DUMMY_PROCESSES_CREATED

        if _DUMMY_PROCESSES_CREATED:
            return
        process_types = [
            ("Background Service", 1),
            ("System Monitor", 3),
            ("File Indexer", 1),
            ("Update Service", 2),
            ("Cache Manager", 1),
            ("Network Service", 2),
            ("Security Scanner", 3),
            ("Backup Service", 1),
            ("Print Spooler", 2),
            ("Search Indexer", 1)
        ]
        for name, priority in process_types:
            self.process_manager.create_process(name, priority, self.memory_manager)
        _DUMMY_PROCESSES_CREATED = True  # Set the global flag after creation




    def terminate_process(self, pid):
        self.process_manager.terminate_process(pid)

    def get_all_processes(self):
        return [
            {
                'pid': p.pid,
                'name': p.name,
                'state': p.state.value,
                'priority': p.priority,
                'cpu_usage': p.cpu_usage,
                'running_time': int(time.time() - p.start_time),
                'page_count': p.memory.page_count  # Include page_count here
            }
            for p in self.process_manager.get_all_processes()
        ]

    def schedule_processes(self):
        while True:
            processes = list(self.process_manager.get_all_processes())
            running = [p for p in processes if p.state == ProcessState.RUNNING]
            ready = [p for p in processes if p.state == ProcessState.READY]
            # Sort by priority (higher number = higher priority)
            ready.sort(key=lambda x: x.priority, reverse=True)

            while len(running) > 3:     # Maximum concurrent running processes 3
                running.pop().change_state(ProcessState.READY)

            while len(running) < 3 and ready:
                p = ready.pop(0)
                p.change_state(ProcessState.RUNNING)
                running.append(p)

            time.sleep(1)       # Schedule every second


class Process:
    def __init__(self, pid, name, start_time):
        self.pid = pid
        self.name = name
        self.start_time = start_time
        self.status = "Running"


class ProcessManager:
    _instance = None
    _next_pid = 1000

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance.processes = {}
        return cls._instance

    def create_process(self, name, priority, memory_manager):
        pid = ProcessManager._next_pid
        ProcessManager._next_pid += 1
        process = DummyProcess(pid, name, priority, memory_manager)
        self.processes[pid] = process
        process.start()
        return pid

    def terminate_process(self, pid):
        if pid in self.processes:
            self.processes[pid].stop()
            del self.processes[pid]
            return True
        return False

    def get_all_processes(self):
        return self.processes.values()



from datetime import datetime

import os
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QLabel, QWidget, QSizePolicy
)
from PyQt5.QtCore import QTimer, QSize, Qt, QDateTime
from PyQt5.QtGui import QIcon, QPalette

class Taskbar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(45)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #2a2a2a, stop:1 #3c3c3c);
                border-top: 1px solid #222;
            }
            QPushButton#startButton {
                background-color: #0078d7;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton#startButton:hover {
                background-color: #005a9e;
            }
            QLabel#clockLabel {
                color: white;
                font-size: 13px;
                padding: 0px 8px;
            }
            QLabel#trayIcon {
                padding: 0px 5px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(10)

        # Start button
        self.start_button = QPushButton()
        self.start_button.setObjectName("startButton")
        icon_path = os.path.join(os.path.dirname(__file__), "start.png")
        self.start_button.setIcon(QIcon(icon_path))
        self.start_button.setIconSize(QSize(28, 28))
        self.start_button.setFixedSize(40, 40)
        layout.addWidget(self.start_button, alignment=Qt.AlignVCenter)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Type here to search")
        self.search_bar.setFixedHeight(30)
        self.search_bar.setFixedWidth(250)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(240, 240, 240, 0.4);
                border: 1px solid #ccc;
                border-radius: 6px;
                padding-left: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        self.search_bar.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_bar, alignment=Qt.AlignVCenter)

        layout.addStretch()

        for name in ["volume", "wifi", "battery"]:
            icon_label = QLabel()
            icon_label.setObjectName("trayIcon")
            icon_path = os.path.join(os.path.dirname(__file__), f"{name}.png")
            icon_label.setPixmap(QIcon(icon_path).pixmap(20, 20))
            icon_label.setToolTip(f"{name.capitalize()} status")
            layout.addWidget(icon_label)

        # Clock
        self.clock_label = QLabel()
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.clock_label.setStyleSheet("""
            QLabel#clockLabel {
                color: white;
                font-size: 13px;
                padding: 0px 8px;
            }
        """)
        layout.addWidget(self.clock_label)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

    def update_clock(self):
        now = QDateTime.currentDateTime()
        time_str = now.toString("hh:mm AP\nddd dd MMM")
        self.clock_label.setText(time_str)

    def perform_search(self):
        query = self.search_bar.text().strip().lower()
        if query:
            # For demo: Show a message box (in real apps, you'd search apps/files/settings)
            QMessageBox.information(self, "Search", f"No results found for \"{query}\".")
        else:
            QMessageBox.warning(self, "Search", "Please type something to search.")

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)


class DesktopIcon(QToolButton):  # Changed from QPushButton
    def __init__(self, icon_path, label, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 110)
        self.setIconSize(QSize(64, 64))
        self.setText(label)
        self.setToolTip(label)
        self.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 11pt;
                text-align: center;
            }
            QToolButton::menu-indicator { image: none; }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
   #     self.clicked.connect(self.activate)
        try:
            if not os.path.exists(icon_path):
                raise FileNotFoundError(f"Icon file not found: {icon_path}")
            self.setIcon(QIcon(icon_path))
        except Exception as e:
            # Use fallback icon
            self.setIcon(QIcon("icons/default.png"))
            print(f"Error loading icon: {e}")

    def activate(self):
        QMessageBox.information(self, "Icon Clicked", f"You clicked on {self.text()}.")


class Window(QFrame):
    def __init__(self, title, width=600, height=400, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QFrame {
                background-color: #222;
                border-radius: 10px;
                border: 2px solid #0078d7;
            }
            QLabel#titleLabel {
                color: white;
                font-weight: bold;
                font-size: 14pt;
                margin-left: 10px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #005a9e;
                border-radius: 7px;
            }
        """)
        self.resize(width, height)
        self.old_pos = None

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Title bar
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(32)
        self.title_bar.setStyleSheet(
            "background-color: #1a1a1a; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.minimize_btn = QPushButton("_")
        self.minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("X")
        self.close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.close_btn)

        self.main_layout.addWidget(self.title_bar)

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.addWidget(self.content_widget)
        self.content_widget.setLayout(self.content_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.pos()):
            self.old_pos = event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        super().mouseReleaseEvent(event)




class StartMenu(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup)
        self.setFixedSize(300, 450)

        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 10px;
            }
            QLineEdit {
                background-color: #2e2e2e;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px 10px;
                color: white;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                text-align: left;
                padding: 8px 10px;
                border: none;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0078d7;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search apps")
        main_layout.addWidget(self.search_bar)

        # App buttons
        self.app_layout = QVBoxLayout()
        app_list = [
            ("File Explorer", "folder.png"),
            ("Notepad", "notepad.png"),
            ("Calculator", "calculator.png"),
            ("Task Manager", "task.png"),
      #     ("Browser", "icons/browser.png"),
      #     ("Settings", "icons/settings.png"),
            ("Terminal", "terminal.png"),
            ("Resource Monitor", "Resource-Monitor.png")
        ]

        for app_name, icon_path in app_list:
            btn = QPushButton(app_name)
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(20, 20))
            btn.clicked.connect(lambda checked, name=app_name: self.launch_app(name))
            self.app_layout.addWidget(btn)

        # Add app list to a container layout
        app_container = QFrame()
        app_container.setLayout(self.app_layout)
        main_layout.addWidget(app_container)

        main_layout.addStretch()

        # Bottom section for user & power (optional)
        bottom_layout = QHBoxLayout()
        user_label = QLabel("👤 Py-OS")
        user_label.setStyleSheet("color: white; font-size: 13px;")
        bottom_layout.addWidget(user_label)

        bottom_layout.addStretch()

        power_btn = QPushButton("⏻")
        power_btn.setToolTip("Shut Down / Sign Out (simulated)")
        power_btn.setFixedSize(32, 32)
        power_btn.setStyleSheet("""
            QPushButton {
                color: white;
                font-size: 14px;
                border-radius: 8px;
                background-color: #333;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        power_btn.clicked.connect(QApplication.instance().quit)
        bottom_layout.addWidget(power_btn)
        main_layout.addLayout(bottom_layout)

    def launch_app(self, app_name):
        try:
            window = None
            desktop = self.parent()

            if app_name == "Calculator":
                window = Calculator(desktop)
            elif app_name == "Notepad":
                window = Notepad(desktop)
            elif app_name == "Task Manager":
                window = TaskManager(desktop)
            elif app_name == "Terminal":
                window = Terminal(desktop)
            elif app_name == "File Explorer":
                window = FileExplorer(desktop)
            elif app_name == "Resource Monitor":
                window = ResourceMonitor(desktop)
            else:
                QMessageBox.information(self, "Launching App", f"Launching {app_name} (simulated).")

            if window:
                window.show()
                desktop.open_windows.append(window)

            self.hide()

        except Exception as e:
            print(f"Error launching {app_name}: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to launch {app_name}: {str(e)}")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap



import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QPoint

class DesktopWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Python OS Desktop")
        self.resize(1280, 720)
        self.setMinimumSize(800, 600)

        self.icons = []
        self.open_windows = []

        # === Wallpaper Layer ===
        self.wallpaper_label = QLabel(self)
        self.wallpaper_label.setScaledContents(True)
        self.wallpaper_label.setGeometry(self.rect())

        image_path = os.path.join(os.path.dirname(__file__), "wallpaper.jpg")
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            print("⚠️ Wallpaper failed to load from:", image_path)
        else:
            print("✅ Wallpaper loaded successfully from:", image_path)
            self.wallpaper_label.setPixmap(
                pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            )

        # === Foreground Layout ===
        self.foreground_layout = QVBoxLayout()
        self.foreground_layout.setContentsMargins(0, 0, 0, 0)
        self.foreground_layout.setSpacing(0)

        # Desktop Icons Layout - changed to vertical layout for vertical icons
        self.desktop_layout = QVBoxLayout()
        self.desktop_layout.setContentsMargins(20, 20, 20, 0)  # smaller margins for neatness
        self.desktop_layout.setSpacing(20)  # vertical space between icons

        # New icons data example (small, vertical, like Windows)
        icons_data = [
            ("folder.png", "File Explorer"),
            ("notepad.png", "Notepad"),
            ("calculator.png", "Calculator"),
            ("task.png", "Task Manager"),
            ("terminal.png", "Terminal"),
            ("Resource-Monitor.png", "Resource Monitor"),
        ]

        for icon_path, label in icons_data:
            icon = DesktopIcon(icon_path, label, self)
            icon.setIconSize(QSize(48, 48))
            self.icons.append(icon)
            self.desktop_layout.addWidget(icon, alignment=Qt.AlignTop | Qt.AlignLeft)

            # Connect desktop icon clicks to launch apps using StartMenu method
            icon.clicked.connect(lambda checked=False, app_name=label: self.launch_app(app_name))

        self.foreground_layout.addLayout(self.desktop_layout)
        self.foreground_layout.addStretch()

        # Taskbar
        self.taskbar = Taskbar()
        self.taskbar.setFixedHeight(40)
        self.taskbar.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.5);
            border-top: 1px solid #555;
        """)
        self.taskbar.start_button.clicked.connect(self.toggle_start_menu)
        self.foreground_layout.addWidget(self.taskbar)

        # Set main layout
        self.setLayout(self.foreground_layout)

        # Start Menu
        self.start_menu = StartMenu(self)
        self.start_menu.hide()
        self.launch_app = self.start_menu.launch_app


    def resizeEvent(self, event):
        # Resize wallpaper to match window
        image_path = os.path.join(os.path.dirname(__file__), "wallpaper.jpg")
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.wallpaper_label.setGeometry(self.rect())
            self.wallpaper_label.setPixmap(
                pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            )
        super().resizeEvent(event)

    def toggle_start_menu(self):
        if self.start_menu.isVisible():
            self.start_menu.hide()
        else:
            pos = self.taskbar.start_button.mapToGlobal(
                QPoint(0, -self.start_menu.height())
            )
            self.start_menu.move(pos)
            self.start_menu.show()
            self.start_menu.raise_()

    def open_app_window(self, title):
        window = Window(title)
        window.setAttribute(Qt.WA_DeleteOnClose)
        window.show()
        self.open_windows.append(window)


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class Calculator(Window):
    DISPLAY_STYLE = """
        QLineEdit {
            background-color: #2c3e50;
            color: white;
            font-size: 24px;
            padding: 10px;
            border: none;
            border-radius: 5px;
        }
    """

    BUTTON_STYLE = """
        QPushButton {
            background-color: #34495e;
            color: white;
            font-size: 18px;
            min-width: 50px;
            min-height: 50px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #3d566e;
        }
        QPushButton:pressed {
            background-color: #2c3e50;
        }
    """

    CLEAR_BUTTON_STYLE = """
        QPushButton {
            background-color: #e74c3c;
            color: white;
            font-size: 18px;
            min-height: 50px;
            border-radius: 6px;
            margin-top: 12px;
        }
        QPushButton:hover {
            background-color: #c0392b;
        }
    """

    def __init__(self, parent=None):
        super().__init__("Calculator", width=300, height=420, parent=parent)

        # Remove previous content
        if hasattr(self, 'content'):
            self.content.setParent(None)
            self.content.deleteLater()

        self.current_equation = ""
        self.pid = ProcessManager().create_process("Calculator",priority=1,memory_manager=MemoryManager())

        # Create and set main layout
        main_content = QWidget()
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        self.display = self.create_display()
        content_layout.addWidget(self.display)

        content_layout.addLayout(self.create_buttons_grid())
        content_layout.addWidget(self.create_clear_button())

        self.layout().addWidget(main_content)

    def create_display(self):
        display = QLineEdit()
        display.setStyleSheet(self.DISPLAY_STYLE)
        display.setFont(QFont("Consolas", 16))
        display.setFixedHeight(50)
        display.setAlignment(Qt.AlignRight)
        display.setReadOnly(True)
        return display

    def create_buttons_grid(self):
        layout = QGridLayout()
        layout.setSpacing(6)

        buttons = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), ('/', 0, 3),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('*', 1, 3),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), ('-', 2, 3),
            ('0', 3, 0), ('.', 3, 1), ('=', 3, 2), ('+', 3, 3),
        ]

        for text, row, col in buttons:
            button = QPushButton(text)
            button.setStyleSheet(self.BUTTON_STYLE)
            button.clicked.connect(lambda _, t=text: self.button_clicked(t))
            layout.addWidget(button, row, col)

        return layout

    def create_clear_button(self):
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(self.CLEAR_BUTTON_STYLE)
        clear_btn.clicked.connect(self.clear_display)
        return clear_btn

    def button_clicked(self, text):
        if text == '=':
            try:
                result = eval(self.current_equation, {"__builtins__": {}}, {})
                self.display.setText(str(result))
                self.current_equation = str(result)
            except Exception:
                self.display.setText("Error")
                self.current_equation = ""
        else:
            self.current_equation += text
            self.display.setText(self.current_equation)

    def clear_display(self):
        self.current_equation = ""
        self.display.setText("")

    def closeEvent(self, event):
        ProcessManager().terminate_process(self.pid)
        super().closeEvent(event)


class ResourceMonitor(Window):
    def __init__(self, parent=None):
        super().__init__("Resource Monitor", width=800, height=450, parent=parent)

        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "State", "Priority", "CPU Usage", "Pages Used"])

        # Header styling
        self.process_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #3c3f41, stop:1 #282a2d);
                color: white;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #4a4a4a;
            }
        """)
        self.process_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        # Column sizing
        self.process_table.setColumnWidth(0, 60)   # PID
        self.process_table.setColumnWidth(2, 100)  # State
        self.process_table.setColumnWidth(3, 80)   # Priority
        self.process_table.setColumnWidth(4, 100)  # CPU Usage
        self.process_table.setColumnWidth(5, 100)  # Pages Used
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Name stretches

        # Style
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                gridline-color: #444;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 13px;
                border: 1px solid #444;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QTableWidget::item:alternate {
                background-color: #252525;
            }
        """)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.content_layout.addWidget(self.process_table)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_process_list)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 6px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #003f6b;
            }
        """)
        self.content_layout.addWidget(self.refresh_btn, alignment=Qt.AlignRight)

        # Timer for periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_process_list)
        self.update_timer.start(1500)

        self.pid = ProcessManager().create_process("Resource Monitor", priority=2, memory_manager=MemoryManager())

        # Initial update
        self.update_process_list()

    def update_process_list(self):
        self.process_table.setRowCount(0)
        processes = ProcessScheduler().get_all_processes()

        for process in processes:
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)

            pid_item = QTableWidgetItem(str(process['pid']))
            pid_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 0, pid_item)

            name_item = QTableWidgetItem(process['name'])
            self.process_table.setItem(row, 1, name_item)

            state_item = QTableWidgetItem(process['state'])
            state_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 2, state_item)

            priority_item = QTableWidgetItem(str(process['priority']))
            priority_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 3, priority_item)

            # CPU Usage
            cpu_val = process['cpu_usage']
            cpu_text = f"{cpu_val}%"
            cpu_item = QTableWidgetItem(cpu_text)
            cpu_item.setTextAlignment(Qt.AlignCenter)
            if cpu_val < 30:
                cpu_item.setForeground(QColor("#6abe30"))
            elif cpu_val < 70:
                cpu_item.setForeground(QColor("#e6b800"))
            else:
                cpu_item.setForeground(QColor("#d9534f"))
            self.process_table.setItem(row, 4, cpu_item)

            # Pages Used
            pages_used = process['page_count']  # Ensure this is correctly retrieved
            page_item = QTableWidgetItem(str(pages_used))
            page_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 5, page_item)

    def closeEvent(self, event):
        ProcessManager().terminate_process(self.pid)
        self.update_timer.stop()
        super().closeEvent(event)



from PyQt5.QtWidgets import (
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QProgressBar, QTableWidgetItem,
    QHeaderView, QTableWidget
)
from PyQt5.QtCore import Qt, QTimer
import time
import random  # for mock CPU/memory usage

class TaskManager(Window):
    def __init__(self, parent=None):
        super().__init__("", width=700, height=500, parent=parent)

        self.setStyleSheet("""
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: white;
                padding: 8px;
            }
            QWidget {
                background-color: #202020;
                color: white;
            }
            QTableWidget {
                background-color: #2a2a2a;
                border: none;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #383838;
                color: white;
                padding: 5px;
                border: 1px solid #444;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                padding: 6px 16px;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #444;
            }
            QPushButton:hover {
                background-color: #0078d7;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)

        # Title
        title_label = QLabel("Task Manager")
        title_label.setObjectName("titleLabel")
        self.content_layout.addWidget(title_label)

        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "Status", "CPU %", "Memory %", "Time"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.content_layout.addWidget(self.process_table)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(0, 10, 0, 0)

        self.refresh_btn = QPushButton("⟳ Refresh")
        self.refresh_btn.clicked.connect(self.update_process_list)
        buttons_layout.addWidget(self.refresh_btn)

        self.end_process_btn = QPushButton("✖ End Task")
        self.end_process_btn.clicked.connect(self.end_selected_process)
        buttons_layout.addWidget(self.end_process_btn)

        self.content_layout.addLayout(buttons_layout)

        # Register Task Manager process
        self.pid = ProcessManager().create_process("Task Manager",priority=3,memory_manager=MemoryManager())

        # Timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_process_list)
        self.update_timer.start(1000)

        self.process_table.itemSelectionChanged.connect(self.update_button_state)

        self.update_process_list()
        self.update_button_state()

    def update_button_state(self):
        selected_items = self.process_table.selectedItems()
        if selected_items:
            pid = int(self.process_table.item(selected_items[0].row(), 0).text())
            self.end_process_btn.setEnabled(pid != self.pid)
        else:
            self.end_process_btn.setEnabled(False)

    def update_process_list(self):
        self.process_table.setRowCount(0)
        processes = sorted(ProcessManager().get_all_processes(), key=lambda p: p.pid)

        for process in processes:
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)

            # PID
            pid_item = QTableWidgetItem(str(process.pid))
            pid_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 0, pid_item)

            # Name
            name_item = QTableWidgetItem(process.name)
            self.process_table.setItem(row, 1, name_item)

            # Status
            status_item = QTableWidgetItem(process.status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 2, status_item)

            # Simulated CPU % bar
            cpu_percent = random.randint(1, 50)
            cpu_bar = QProgressBar()
            cpu_bar.setValue(cpu_percent)
            cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #4caf50; }")
            self.process_table.setCellWidget(row, 3, cpu_bar)

            # Simulated Memory % bar
            mem_percent = random.randint(1, 80)
            mem_bar = QProgressBar()
            mem_bar.setValue(mem_percent)
            mem_bar.setStyleSheet("QProgressBar::chunk { background-color: #2196f3; }")
            self.process_table.setCellWidget(row, 4, mem_bar)

            # Time
            running_time = int(time.time() - process.start_time)
            minutes = running_time // 60
            seconds = running_time % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 5, time_item)

    def end_selected_process(self):
        selected_items = self.process_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            pid = int(self.process_table.item(row, 0).text())

            if pid == self.pid:
                return

            for window in self.parent().findChildren(Window):
                if hasattr(window, 'pid') and window.pid == pid:
                    window.close()
                    break

            ProcessManager().terminate_process(pid)
            self.update_process_list()
            self.update_button_state()

    def closeEvent(self, event):
        self.update_timer.stop()
        ProcessManager().terminate_process(self.pid)
        super().closeEvent(event)


class Notepad(Window):
    def __init__(self, parent=None):
        super().__init__("Untitled - Notepad", width=600, height=400, parent=parent)

        # Menu bar styled for dark theme
        self.menu_bar = QMenuBar()
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #2e2e2e;
                color: #ddd;
                border-bottom: 1px solid #444;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 12pt;
            }
            QMenuBar::item {
                spacing: 3px;
                padding: 4px 12px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background-color: #3a6fd6;
                color: white;
            }
            QMenu {
                background-color: #2e2e2e;
                border: 1px solid #444;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 12pt;
                color: #ddd;
            }
            QMenu::item:selected {
                background-color: #3a6fd6;
                color: white;
            }
        """)

        file_menu = self.menu_bar.addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        self.main_layout.insertWidget(1, self.menu_bar)

        # Text editor with dark theme styling
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #f0f0f0;
                border: 1px solid #444;
                font-family: 'Consolas', monospace;
                font-size: 12pt;
                padding: 8px;
                selection-background-color: #3a6fd6;
                selection-color: white;
            }
            QTextEdit:focus {
                border: 1px solid #6a94ff;
            }
        """)
        self.content_layout.addWidget(self.text_edit)

        self.current_file = None

        self.pid = ProcessManager().create_process("Notepad",priority=1,memory_manager=MemoryManager())

    def new_file(self):
        if self.maybe_save():
            self.text_edit.clear()
            self.current_file = None
            self.setWindowTitle("Untitled - Notepad")

    def open_file(self):
        if self.maybe_save():
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Open File",
                "",
                "Text Files (*.txt);;All Files (*)"
            )
            if file_name:
                try:
                    with open(file_name, 'r', encoding='utf-8') as file:
                        self.text_edit.setPlainText(file.read())
                    self.current_file = file_name
                    self.setWindowTitle(f"{os.path.basename(file_name)} - Notepad")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")

    def save_file(self):
        if self.current_file:
            return self.save_file_as(self.current_file)
        return self.save_file_as()

    def save_file_as(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save File",
                "",
                "Text Files (*.txt);;All Files (*)"
            )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_edit.toPlainText())
                self.current_file = file_path
                self.setWindowTitle(f"{os.path.basename(file_path)} - Notepad")
                self.text_edit.document().setModified(False)
                return True
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
        return False

    def maybe_save(self):
        if not self.text_edit.document().isModified():
            return True

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Save Changes")
        msg_box.setText("Do you want to save the changes you made?")
        msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Save)

        # Dark style for QMessageBox
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2e2e2e;
                color: #ddd;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 12pt;
                border: 1px solid #444;
            }
            QPushButton {
                background-color: #3a6fd6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a54b0;
            }
            QPushButton:pressed {
                background-color: #1f3c7a;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """)

        reply = msg_box.exec()

        if reply == QMessageBox.Save:
            return self.save_file()
        elif reply == QMessageBox.Cancel:
            return False
        return True

    def closeEvent(self, event):
        if self.maybe_save():
            ProcessManager().terminate_process(self.pid)
            event.accept()
        else:
            event.ignore()



class Terminal(Window):
    def __init__(self, parent=None):
        super().__init__("Terminal", width=700, height=450, parent=parent)

        # Terminal output (read-only, multiline)
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                border: none;
                padding: 10px;
            }
        """)
        self.content_layout.addWidget(self.terminal_output)

        # Command input (single-line)
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                border: none;
                padding: 8px;
            }
            QLineEdit:focus {
                outline: none;
            }
        """)
        self.command_input.returnPressed.connect(self.execute_command)
        self.content_layout.addWidget(self.command_input)

        # Set initial current directory to user's home folder (more Windows-like)
        # Set initial current directory to actual location
        self.current_dir = r"C:\Users\anasa\OneDrive\Desktop\GBS\Py-OS\My PC"

        # Set display name (e.g., to mimic 'C:' instead of long path)
        self.display_name = "C:"

        # Display welcome message and prompt
        self.write_output("Welcome to Py-OS Terminal (Windows Based)")
        self.display_prompt()

        # Register process
        self.pid = ProcessManager().create_process("Terminal",priority=3,memory_manager=MemoryManager())

    def write_output(self, text):
        self.terminal_output.append(text)
        # Auto-scroll to bottom after new output
        scrollbar = self.terminal_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def display_prompt(self):
        prompt_text = f"{self.display_name}> "
        self.write_output(prompt_text)
        self.command_input.setFocus()

    def execute_command(self):
        command = self.command_input.text().strip()
        if not command:
            self.display_prompt()
            self.command_input.clear()
            return

        # Echo the command input in output window (like real terminals do)
        folder_name = os.path.basename(self.current_dir) or self.current_dir
        self.write_output(f"{self.display_name}> {command}")

        self.command_input.clear()

        try:
            # Handle cd separately for better path management
            if command.startswith("cd"):
                parts = command.split(maxsplit=1)
                if len(parts) == 1 or parts[1] == "":
                    # cd without args goes to home dir
                    new_dir = os.path.expanduser("~")
                else:
                    new_dir = parts[1].strip().replace('"', '')

                    # Handle relative and absolute paths
                    if not os.path.isabs(new_dir):
                        new_dir = os.path.join(self.current_dir, new_dir)

                if os.path.isdir(new_dir):
                    self.current_dir = os.path.normpath(new_dir)
                else:
                    self.write_output(f"System cannot find the path specified: {new_dir}")

            elif command in ["dir", "ls"]:
                # List directory contents with details like Windows 'dir'
                try:
                    entries = os.listdir(self.current_dir)
                    entries.sort()
                    output_lines = []
                    for e in entries:
                        full_path = os.path.join(self.current_dir, e)
                        if os.path.isdir(full_path):
                            output_lines.append(f"<DIR>       {e}")
                        else:
                            size = os.path.getsize(full_path)
                            output_lines.append(f"          {size:>10} {e}")
                    self.write_output("\n".join(output_lines))
                except Exception as e:
                    self.write_output(f"Error listing directory: {e}")

            elif command == "cls":
                # Clear screen command
                self.terminal_output.clear()

            elif command == "pwd":
                self.write_output(self.current_dir)

            else:
                # Execute other commands via subprocess for safety and output capture
                import subprocess
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=self.current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                if stdout:
                    self.write_output(stdout.strip())
                if stderr:
                    self.write_output(stderr.strip())

        except Exception as e:
            self.write_output(f"Error: {str(e)}")

        self.display_prompt()

    def closeEvent(self, event):
        ProcessManager().terminate_process(self.pid)
        super().closeEvent(event)



class FileExplorer(Window):
    def __init__(self, parent=None):
        super().__init__("File Explorer", width=800, height=600, parent=parent)

        self.base_path = os.path.join(os.getcwd(), "My PC")
        os.makedirs(self.base_path, exist_ok=True)
        self.current_path = self.base_path
        self.history = [self.current_path]
        self.history_index = 0

        path_layout = QHBoxLayout()
        self.back_btn = self.create_nav_btn("←", self.go_back)
        self.forward_btn = self.create_nav_btn("→", self.go_forward)
        self.up_btn = self.create_nav_btn("↑", self.go_up)

        for btn in [self.back_btn, self.forward_btn, self.up_btn]:
            path_layout.addWidget(btn)

        self.path_input = QLineEdit()
        self.path_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                padding: 6px 10px;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        self.path_input.returnPressed.connect(self.navigate_to_path)
        path_layout.addWidget(self.path_input)
        self.content_layout.addLayout(path_layout)

        self.file_list = QTableWidget()
        self.file_list.setColumnCount(4)
        self.file_list.setHorizontalHeaderLabels(["Name", "Size", "Type", "Modified"])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.file_list.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                gridline-color: #2a2a2a;
                border: 1px solid #2d2d2d;
                font-size: 13px;
                border-radius: 6px;
                selection-background-color: #0a84ff;
                selection-color: white;
            }
            QTableWidget:focus {
                outline: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-bottom: 1px solid #444;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #0a84ff;
                color: white;
            }
        """)
        self.file_list.doubleClicked.connect(self.item_double_clicked)
        self.content_layout.addWidget(self.file_list)

        self.pid = ProcessManager().create_process("File Explorer",priority=2,memory_manager=MemoryManager())
        self.update_view()

    def create_nav_btn(self, label, action):
        btn = QPushButton(label)
        btn.setFixedWidth(30)
        btn.clicked.connect(action)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                border: 1px solid #444;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        return btn

    def update_view(self):
        self.path_input.setText(self.pretty_path(self.current_path))
        self.file_list.setRowCount(0)

        try:
            items = os.listdir(self.current_path)
            for item in sorted(items):
                full_path = os.path.join(self.current_path, item)
                row = self.file_list.rowCount()
                self.file_list.insertRow(row)

                if self.current_path == self.base_path and item.lower().startswith("local disk"):
                    icon = QIcon("disk.png")
                elif os.path.isdir(full_path):
                    icon = QIcon.fromTheme("folder")
                else:
                    icon = QIcon.fromTheme("text-x-generic")

                name_item = QTableWidgetItem(icon, item)
                self.file_list.setItem(row, 0, name_item)

                try:
                    stats = os.stat(full_path)

                    size_str = "-"
                    if os.path.isfile(full_path):
                        size = stats.st_size
                        size_str = (
                            f"{size / (1024 * 1024):.1f} MB" if size > 1024 * 1024 else
                            f"{size / 1024:.1f} KB" if size > 1024 else
                            f"{size:,} B"
                        )
                    self.file_list.setItem(row, 1, QTableWidgetItem(size_str))

                    type_str = "Folder" if os.path.isdir(full_path) else "File"
                    self.file_list.setItem(row, 2, QTableWidgetItem(type_str))

                    mod_time = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
                    self.file_list.setItem(row, 3, QTableWidgetItem(mod_time))

                except Exception as e:
                    print(f"Stat error: {e}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot open folder: {e}")

    def pretty_path(self, full_path):
        if full_path.startswith(self.base_path):
            rel = os.path.relpath(full_path, self.base_path)
            return "My PC" if rel == "." else f"My PC/{rel.replace(os.sep, '/')}"
        return full_path

    def real_path(self, pretty):
        if pretty.startswith("My PC"):
            rest = pretty[6:].strip("/").replace("/", os.sep)
            return os.path.join(self.base_path, rest)
        return pretty

    def navigate_to_path(self):
        path = self.real_path(self.path_input.text())
        if os.path.exists(path) and os.path.isdir(path):
            self.add_to_history(path)
            self.current_path = path
            self.update_view()
        else:
            QMessageBox.warning(self, "Invalid Path", "The entered path does not exist.")

    def item_double_clicked(self, index):
        name = self.file_list.item(index.row(), 0).text()
        path = os.path.join(self.current_path, name)
        if os.path.isdir(path):
            self.add_to_history(path)
            self.current_path = path
            self.update_view()

    def add_to_history(self, path):
        self.history_index += 1
        self.history = self.history[:self.history_index]
        self.history.append(path)

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_path = self.history[self.history_index]
            self.update_view()

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_path = self.history[self.history_index]
            self.update_view()

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path and os.path.commonpath([self.base_path, parent]) == self.base_path:
            self.add_to_history(parent)
            self.current_path = parent
            self.update_view()

    def closeEvent(self, event):
        ProcessManager().terminate_process(self.pid)
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    desktop_window = DesktopWindow()
    desktop_window.show()
    #desktop_window.showFullScreen()
    sys.exit(app.exec_())