import sys
import warnings

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
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QBrush, QLinearGradient, QColor, QFontDatabase, QFont, QPainter
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


class ProcessState(Enum):
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    BLOCKED = "Blocked"
    TERMINATED = "Terminated"


class DummyProcess:
    def __init__(self, pid, name, priority):
        self.pid = pid
        self.name = name
        self.priority = priority
        self.state = ProcessState.READY
        self.cpu_usage = 0
        self.start_time = time.time()
        self.last_state_change = time.time()
        self.thread = None
        self.is_running = True

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


class ProcessScheduler:
    def __init__(self):
        self.processes = {}
        self.current_pid = 2000  # Starting PID

        # Create dummy processes
        self.create_dummy_processes()

        # Start scheduler thread
        self.scheduler_thread = Thread(target=self.schedule_processes, daemon=True)
        self.scheduler_thread.start()

    def create_dummy_processes(self):
        process_types = [
            ("Background Service", 1),  # Low priority
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
            self.create_process(name, priority)

    def create_process(self, name, priority):
        pid = self.current_pid
        self.current_pid += 1

        process = DummyProcess(pid, name, priority)
        self.processes[pid] = process
        process.start()
        return pid

    def terminate_process(self, pid):
        if pid in self.processes:
            self.processes[pid].stop()
            del self.processes[pid]

    def get_all_processes(self):
        return [
            {
                'pid': p.pid,
                'name': p.name,
                'state': p.state.value,
                'priority': p.priority,
                'cpu_usage': p.cpu_usage,
                'running_time': int(time.time() - p.start_time)
            }
            for p in self.processes.values()
        ]

    def schedule_processes(self):
        while True:
            running_processes = [p for p in self.processes.values() if p.state == ProcessState.RUNNING]
            ready_processes = [p for p in self.processes.values() if p.state == ProcessState.READY]

            # Sort by priority (higher number = higher priority)
            ready_processes.sort(key=lambda x: x.priority, reverse=True)

            max_running = 3  # Maximum concurrent running processes

            # Stop excess running processes
            while len(running_processes) > max_running:
                process = running_processes.pop()
                process.change_state(ProcessState.READY)

            # Start ready processes if we have capacity
            while len(running_processes) < max_running and ready_processes:
                process = ready_processes.pop(0)
                process.change_state(ProcessState.RUNNING)
                running_processes.append(process)  # Add to running processes list

            time.sleep(1)  # Schedule every second


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

    def create_process(self, name):
        pid = ProcessManager._next_pid
        ProcessManager._next_pid += 1
        process = Process(pid, name, time.time())
        self.processes[pid] = process
        return pid

    def terminate_process(self, pid):
        if pid in self.processes:
            del self.processes[pid]
            return True
        return False

    def get_all_processes(self):
        return self.processes.values()


class Taskbar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #2a2a2a, stop:1 #444444);
                border-top: 1px solid #333;
            }
            QPushButton#startButton {
                background-color: #0078d7;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton#startButton:hover {
                background-color: #005a9e;
            }
            QLabel#clockLabel {
                color: white;
                font-size: 12pt;
                padding: 0px 10px;
            }
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(15)

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.start_button.setFixedSize(80, 30)
        layout.addWidget(self.start_button, alignment=Qt.AlignVCenter | Qt.AlignLeft)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(spacer)

        self.clock_label = QLabel()
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.clock_label, alignment=Qt.AlignVCenter | Qt.AlignRight)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

    def update_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.setText(now)

    def closeEvent(self, event):
        """Properly clean up resources when widget is closed."""
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
        self.clicked.connect(self.activate)
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
        self.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 2px solid #0078d7;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.setFixedSize(220, 350)
        layout = QVBoxLayout()
        self.setLayout(layout)

        app_list = [
            ("File Explorer", "icons/folder.png"),
            ("Notepad", "icons/notepad.png"),
            ("Calculator", "icons/calculator.png"),
            ("Task Manager", "icons/task-manager.png"),
            ("Browser", "icons/browser.png"),
            ("Settings", "icons/settings.png"),
            ("Terminal", "icons/terminal.png"),
            ("Resource Monitor", "icons/Resource-Monitor.png")
        ]

        for app_name, icon_path in app_list:
            btn = QPushButton(app_name)
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(24, 24))
            btn.clicked.connect(lambda checked, name=app_name: self.launch_app(name))
            layout.addWidget(btn)

        layout.addStretch()

    def launch_app(self, app_name):
        try:
            window = None
            desktop = self.parent()  # Get the DesktopWindow instance

            # Create new window, passing the desktop as parent
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
                desktop.open_windows.append(window)  # Add to the list of open windows
            self.hide()

        except Exception as e:
            print(f"Error launching {app_name}: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to launch {app_name}: {str(e)}")


class DesktopWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.open_windows = []  # Keep track of open windows
        self.setWindowTitle("Python OS Desktop")
        self.resize(1024, 700)
        self.setMinimumSize(800, 600)

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #004080, stop:1 #0066cc);
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            }
        """)

        self.icons = []

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Desktop icon layout
        self.desktop_layout = QHBoxLayout()
        self.desktop_layout.setContentsMargins(20, 20, 20, 0)
        self.desktop_layout.setSpacing(40)

        # Add icons
        icons_data = [
            ("icons/folder.png", "Documents"),
            ("icons/folder.png", "Pictures"),
            ("icons/folder.png", "Music"),
            ("icons/folder.png", "Videos"),
            ("icons/trash.png", "Recycle Bin"),
        ]

        for icon_path, label in icons_data:
            icon = DesktopIcon(icon_path, label, self)
            self.icons.append(icon)
            self.desktop_layout.addWidget(icon)

        layout.addLayout(self.desktop_layout)
        layout.addStretch()

        # Taskbar
        self.taskbar = Taskbar()
        self.taskbar.start_button.clicked.connect(self.toggle_start_menu)
        layout.addWidget(self.taskbar)

        self.setLayout(layout)

        self.start_menu = StartMenu(self)
        self.start_menu.hide()

        self.open_windows = []

    def toggle_start_menu(self):
        if self.start_menu.isVisible():
            self.start_menu.hide()
        else:
            pos = self.taskbar.start_button.mapToGlobal(QPoint(0, -self.start_menu.height()))
            self.start_menu.move(pos)
            self.start_menu.show()
            self.start_menu.raise_()

    def open_app_window(self, title):
        window = Window(title)
        window.setAttribute(Qt.WA_DeleteOnClose)
        window.show()
        self.open_windows.append(window)


class Calculator(Window):
    def __init__(self, parent=None):
        super().__init__("Calculator", width=300, height=400, parent=parent)

        # Replace default content
        if hasattr(self, 'content'):
            self.content.setParent(None)
            self.content.deleteLater()

        # Create main content widget and layout
        main_content = QWidget()
        content_layout = QVBoxLayout()
        main_content.setLayout(content_layout)

        # Display
        self.display = QLineEdit()
        self.display.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                font-size: 24px;
                padding: 10px;
                border: 1px solid #444;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        self.display.setFixedHeight(50)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        content_layout.addWidget(self.display)

        # Buttons grid
        buttons_widget = QWidget()
        button_grid = QGridLayout()
        buttons_widget.setLayout(button_grid)
        button_grid.setSpacing(5)

        buttons = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), ('/', 0, 3),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('*', 1, 3),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), ('-', 2, 3),
            ('0', 3, 0), ('.', 3, 1), ('=', 3, 2), ('+', 3, 3),
        ]

        for button_text, row, col in buttons:
            button = QPushButton(button_text)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    font-size: 18px;
                    min-width: 50px;
                    min-height: 50px;
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
                QPushButton:pressed {
                    background-color: #666;
                }
            """)
            button.clicked.connect(lambda checked, text=button_text: self.button_clicked(text))
            button_grid.addWidget(button, row, col)

        content_layout.addWidget(buttons_widget)

        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #d35400;
                color: white;
                font-size: 18px;
                min-height: 50px;
                border-radius: 5px;
                padding: 5px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        clear_button.clicked.connect(self.clear_display)
        content_layout.addWidget(clear_button)

        # Add the main content widget to the window layout
        self.layout().addWidget(main_content)

        self.current_equation = ""

        # Register process
        self.pid = ProcessManager().create_process("Calculator")

    def button_clicked(self, text):
        if text == '=':
            try:
                # Evaluate the expression safely
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
        super().__init__("Resource Monitor", width=600, height=400, parent=parent)

        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)  # Update to 5 columns
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "State", "Priority", "CPU Usage"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.setStyleSheet("""
            QTableWidget {
                background-color: #333;
                color: white;
                gridline-color: #444;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
            }
        """)
        self.content_layout.addWidget(self.process_table)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_process_list)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.content_layout.addWidget(self.refresh_btn)

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_process_list)
        self.update_timer.start(1000)  # Update every second
        self.pid = ProcessManager().create_process("Resource Monitor")
        # Initial update
        self.update_process_list()

    def update_process_list(self):
        self.process_table.setRowCount(0)
        processes = ProcessScheduler().get_all_processes()  # Get processes from ProcessScheduler

        for process in processes:
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)

            # PID
            pid_item = QTableWidgetItem(str(process['pid']))
            pid_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 0, pid_item)

            # Name
            name_item = QTableWidgetItem(process['name'])
            self.process_table.setItem(row, 1, name_item)

            # State
            state_item = QTableWidgetItem(process['state'])
            state_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 2, state_item)

            # Priority
            priority_item = QTableWidgetItem(str(process['priority']))
            priority_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 3, priority_item)

            # CPU Usage
            cpu_usage_item = QTableWidgetItem(f"{process['cpu_usage']}%")
            cpu_usage_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 4, cpu_usage_item)

    def closeEvent(self, event):
        ProcessManager().terminate_process(self.pid)
        self.update_timer.stop()
        super().closeEvent(event)


class TaskManager(Window):
    def __init__(self, parent=None):
        super().__init__("Task Manager", width=500, height=400, parent=parent)

        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "Status", "Running Time"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.setStyleSheet("""
            QTableWidget {
                background-color: #333;
                color: white;
                gridline-color: #444;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
            }
        """)
        self.content_layout.addWidget(self.process_table)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_process_list)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        buttons_layout.addWidget(self.refresh_btn)

        # End Process button
        self.end_process_btn = QPushButton("End Process")
        self.end_process_btn.clicked.connect(self.end_selected_process)
        self.end_process_btn.setStyleSheet("""
            QPushButton {
                background-color: #d35400;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        buttons_layout.addWidget(self.end_process_btn)

        self.content_layout.addLayout(buttons_layout)

        # Register as process
        self.pid = ProcessManager().create_process("Task Manager")

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_process_list)
        self.update_timer.start(1000)  # Update every second

        # Initial update
        self.update_process_list()

        # Connect selection change to update button state
        self.process_table.itemSelectionChanged.connect(self.update_button_state)

        # Initial button state
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

            # Running Time
            running_time = int(time.time() - process.start_time)
            minutes = running_time // 60
            seconds = running_time % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 3, time_item)

    def end_selected_process(self):
        selected_items = self.process_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            pid = int(self.process_table.item(row, 0).text())

            # Don't allow terminating self
            if pid == self.pid:
                return

            # Find the window associated with this PID
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
        super().__init__("Notepad", width=600, height=400, parent=parent)

        # Create menu bar
        self.menu_bar = QMenuBar()
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #333;
                color: white;
                border: none;
            }
            QMenuBar::item:selected {
                background-color: #0078d7;
            }
            QMenu {
                background-color: #333;
                color: white;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #0078d7;
            }
        """)

        # File menu
        file_menu = self.menu_bar.addMenu("File")

        # New file action
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # Open file action
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Save action
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Save As action
        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        self.main_layout.insertWidget(1, self.menu_bar)

        # Create text editor
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 12pt;
            }
        """)
        self.content_layout.addWidget(self.text_edit)

        # Keep track of current file
        self.current_file = None

        # Register process
        self.pid = ProcessManager().create_process("Notepad")

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
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Could not open file: {str(e)}"
                    )

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
                return True
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Could not save file: {str(e)}"
                )
        return False

    def maybe_save(self):
        if not self.text_edit.document().isModified():
            return True

        reply = QMessageBox.warning(
            self,
            "Save Changes",
            "Do you want to save the changes you made?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )

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


class TaskManager(Window):
    def __init__(self, parent=None):
        super().__init__("Task Manager", width=500, height=400, parent=parent)

        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "Status", "Running Time"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.setStyleSheet("""
            QTableWidget {
                background-color: #333;
                color: white;
                gridline-color: #444;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078d7;
            }
        """)
        self.content_layout.addWidget(self.process_table)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_process_list)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        buttons_layout.addWidget(self.refresh_btn)

        # End Process button
        self.end_process_btn = QPushButton("End Process")
        self.end_process_btn.clicked.connect(self.end_selected_process)
        self.end_process_btn.setStyleSheet("""
            QPushButton {
                background-color: #d35400;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        buttons_layout.addWidget(self.end_process_btn)

        self.content_layout.addLayout(buttons_layout)

        # Register as process
        self.pid = ProcessManager().create_process("Task Manager")

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_process_list)
        self.update_timer.start(1000)  # Update every second

        # Initial update
        self.update_process_list()

        # Connect selection change to update button state
        self.process_table.itemSelectionChanged.connect(self.update_button_state)

        # Initial button state
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

            # Running Time
            running_time = int(time.time() - process.start_time)
            minutes = running_time // 60
            seconds = running_time % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.process_table.setItem(row, 3, time_item)

    def end_selected_process(self):
        selected_items = self.process_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            pid = int(self.process_table.item(row, 0).text())

            # Don't allow terminating self
            if pid == self.pid:
                return

            # Find the window associated with this PID
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


class Terminal(Window):
    def __init__(self, parent=None):
        super().__init__("Terminal", width=600, height=400, parent=parent)

        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                border: none;
                padding: 5px;
            }
        """)
        self.content_layout.addWidget(self.terminal_output)

        # Command input
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                border: none;
                padding: 5px;
            }
        """)
        self.command_input.returnPressed.connect(self.execute_command)
        self.content_layout.addWidget(self.command_input)

        # Current working directory
        self.current_dir = os.getcwd()

        # Initialize terminal
        self.write_output(f"Welcome to Python Terminal\n{self.current_dir}$ ")

        # Register process
        self.pid = ProcessManager().create_process("Terminal")

    def write_output(self, text):
        self.terminal_output.append(text)

    def execute_command(self):
        command = self.command_input.text().strip()
        self.write_output(command)
        self.command_input.clear()

        try:
            if command.startswith('cd '):
                # Change directory
                new_dir = command[3:].strip()
                if os.path.exists(new_dir):
                    os.chdir(new_dir)
                    self.current_dir = os.getcwd()
                else:
                    self.write_output("Directory not found")

            elif command == 'ls' or command == 'dir':
                # List directory contents
                files = os.listdir(self.current_dir)
                self.write_output('\n'.join(files))

            elif command == 'pwd':
                # Print working directory
                self.write_output(self.current_dir)

            elif command:
                # Execute other commands
                result = os.popen(command).read()
                self.write_output(result)

        except Exception as e:
            self.write_output(f"Error: {str(e)}")

        self.write_output(f"\n{self.current_dir}$ ")

    def closeEvent(self, event):
        ProcessManager().terminate_process(self.pid)
        super().closeEvent(event)


class FileExplorer(Window):
    def __init__(self, parent=None):
        super().__init__("File Explorer", width=800, height=600, parent=parent)

        # Path bar layout
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                padding: 5px;
                border: 1px solid #444;
                border-radius: 3px;
            }
        """)
        self.path_input.returnPressed.connect(self.navigate_to_path)

        # Navigation buttons
        self.back_btn = QPushButton("←")
        self.forward_btn = QPushButton("→")
        self.up_btn = QPushButton("↑")
        for btn in [self.back_btn, self.forward_btn, self.up_btn]:
            btn.setFixedWidth(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)
            path_layout.addWidget(btn)

        path_layout.addWidget(self.path_input)
        self.content_layout.addLayout(path_layout)

        # File list
        self.file_list = QTableWidget()
        self.file_list.setColumnCount(4)
        self.file_list.setHorizontalHeaderLabels(["Name", "Size", "Type", "Modified"])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.setStyleSheet("""
            QTableWidget {
                background-color: #333;
                color: white;
                gridline-color: #444;
                border: 1px solid #444;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
        """)
        self.file_list.doubleClicked.connect(self.item_double_clicked)
        self.content_layout.addWidget(self.file_list)

        # Initialize path and history
        self.current_path = os.getcwd()
        self.history = [self.current_path]
        self.history_index = 0

        # Connect navigation buttons
        self.back_btn.clicked.connect(self.go_back)
        self.forward_btn.clicked.connect(self.go_forward)
        self.up_btn.clicked.connect(self.go_up)

        # Update view
        self.update_view()

        # Register process
        self.pid = ProcessManager().create_process("File Explorer")

    def update_view(self):
        self.path_input.setText(self.current_path)
        self.file_list.setRowCount(0)

        try:
            items = os.listdir(self.current_path)
            for item in sorted(items):
                path = os.path.join(self.current_path, item)
                row = self.file_list.rowCount()
                self.file_list.insertRow(row)

                # Name
                self.file_list.setItem(row, 0, QTableWidgetItem(item))

                try:
                    stats = os.stat(path)

                    # Size
                    size = stats.st_size
                    size_str = f"{size:,} bytes"
                    if size > 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    elif size > 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    self.file_list.setItem(row, 1, QTableWidgetItem(size_str))

                    # Type
                    type_str = "Directory" if os.path.isdir(path) else "File"
                    self.file_list.setItem(row, 2, QTableWidgetItem(type_str))

                    # Modified time
                    mod_time = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
                    self.file_list.setItem(row, 3, QTableWidgetItem(mod_time))

                except Exception as e:
                    print(f"Error getting file info: {e}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot access directory: {str(e)}")

    def navigate_to_path(self):
        path = self.path_input.text()
        if os.path.exists(path):
            self.add_to_history(path)
            self.current_path = path
            self.update_view()

    def item_double_clicked(self, index):
        item = self.file_list.item(index.row(), 0)
        path = os.path.join(self.current_path, item.text())
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
        if parent != self.current_path:
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
    sys.exit(app.exec_())
