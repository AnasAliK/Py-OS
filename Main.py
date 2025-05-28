import sys
import os
from PyQt5.QtWidgets import (
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

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Title bar
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(32)
        self.title_bar.setStyleSheet(
            "background-color: #1a1a1a; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        title_layout = QHBoxLayout()
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
        self.title_bar.setLayout(title_layout)

        layout.addWidget(self.title_bar)

        # Content area
        self.content = QLabel(f"This is the {title} window content area.")
        self.content.setStyleSheet("color: white; padding: 15px;")
        layout.addWidget(self.content)

        self.setLayout(layout)

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
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 12pt;
                border: none;
                padding: 8px 15px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #0078d7;
                border-radius: 5px;
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
        ]

        for app_name, icon_path in app_list:
            btn = QPushButton(app_name)
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(24, 24))
            btn.clicked.connect(lambda checked, name=app_name: self.launch_app(name))
            layout.addWidget(btn)

        layout.addStretch()

    def launch_app(self, app_name):
        window = None

        # Check if the app is already running
        for existing_window in self.parent().findChildren(Window):
            if isinstance(existing_window, TaskManager) and app_name == "Task Manager":
                existing_window.activateWindow()
                existing_window.raise_()
                self.hide()
                return

        # Create new window
        if app_name == "Calculator":
            window = Calculator(self.parent())
        elif app_name == "Notepad":
            window = Notepad(self.parent())
        elif app_name == "Task Manager":
            window = TaskManager(self.parent())
        else:
            QMessageBox.information(self, "Launching App", f"Launching {app_name} (simulated).")

        if window:
            window.show()
        self.hide()


class DesktopWindow(QWidget):
    def __init__(self):
        super().__init__()
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


class TaskManager(Window):
    def __init__(self, parent=None):
        super().__init__("Task Manager", width=500, height=400, parent=parent)

        # Replace default content
        self.content.setParent(None)
        self.content.deleteLater()

        # Create main content widget and layout
        main_content = QWidget()
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(10, 10, 10, 10)

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

        content_layout.addWidget(self.process_table)

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

        content_layout.addLayout(buttons_layout)

        # Add the main content widget to the window layout
        self.layout().addWidget(main_content)

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

        # Replace default content with text editor
        self.content.deleteLater()

        content_layout = QVBoxLayout()

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                color: white;
                font-family: Consolas, monospace;
                font-size: 14px;
                padding: 10px;
                border: 1px solid #444;
                border-radius: 5px;
            }
        """)
        content_layout.addWidget(self.text_edit)

        # Add the content layout to main layout
        main_content = QWidget()
        main_content.setLayout(content_layout)
        self.layout().addWidget(main_content)

        # Register process
        self.pid = ProcessManager().create_process("Notepad")

    def closeEvent(self, event):
        ProcessManager().terminate_process(self.pid)
        super().closeEvent(event)


def main():
    try:
        app = QApplication(sys.argv)

        # Load icons from the same directory or specify paths properly
        # You can create a folder named 'icons' and put some PNG icons for the desktop icons

        desktop = DesktopWindow()
        desktop.show()

        return app.exec_()
    except Exception as e:
        print(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())