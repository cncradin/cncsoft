from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from laser_preview_widget import LaserPreviewWidget  # ایمپورت از فایل جدید

class SimulationDialog(QDialog):
    def __init__(self, parent, gcode_lines, worktable_width, worktable_height):
        super().__init__(parent)
        self.setWindowTitle("Simulation Window")
        self.setMinimumSize(1350, 700)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        # Layout اصلی
        main_layout = QVBoxLayout(self)

        # ویجت پیش‌نمایش شبیه‌سازی
        self.preview_widget = LaserPreviewWidget(self)
        main_layout.addWidget(self.preview_widget)

        # لایه کنترل‌ها (دکمه‌های اضافی برای گسترش آینده)
        control_layout = QHBoxLayout()
        self.close_button = QPushButton("Close", self)
        self.close_button.setFixedSize(100, 30)
        self.close_button.clicked.connect(self.accept)
        control_layout.addStretch()
        control_layout.addWidget(self.close_button)
        main_layout.addLayout(control_layout)

        # تنظیم داده‌های شبیه‌سازی
        self.preview_widget.set_simulation_data(gcode_lines, worktable_width, worktable_height)

        # اتصال سیگنال‌ها
        self.preview_widget.status_message.connect(self.parent().update_status_label)