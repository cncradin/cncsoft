from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QGraphicsScene, QGraphicsView, QGraphicsLineItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, QPropertyAnimation, QObject, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter
import math
import re

class PositionHelper(QObject):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
        self._pos = item.pos()

    @pyqtProperty(QPointF)
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        self.item.setPos(value)

class LaserPreviewWidget(QWidget):
    status_message = pyqtSignal(str)
    highlight_gcode_line = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.gcode_paths = []
        self.gcode_line_indices = []
        self.line_items = []
        self.speed = 500
        self.worktable_width = 1300
        self.worktable_height = 900
        self.animations = []
        self.current_line_index = 0
        self.is_paused = False
        self.is_stepping = False
        self.min_x = 0
        self.max_x = 0
        self.min_y = 0
        self.max_y = 0
        self.laser_head = None
        self.current_position = None
        self.position_helper = None
        self.traversed_lines = set()  # برای ذخیره ایندکس خطوط طی‌شده

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.controls_layout = QHBoxLayout()
        self.run_button = QPushButton(self)
        self.run_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.run_button.setFixedSize(40, 40)
        self.run_button.clicked.connect(self.run_simulation)
        self.controls_layout.addWidget(self.run_button)

        self.pause_button = QPushButton(self)
        self.pause_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        self.pause_button.setFixedSize(40, 40)
        self.pause_button.clicked.connect(self.pause_simulation)
        self.controls_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton(self)
        self.stop_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        self.stop_button.setFixedSize(40, 40)
        self.stop_button.clicked.connect(self.stop_simulation)
        self.controls_layout.addWidget(self.stop_button)

        self.step_forward_button = QPushButton(self)
        self.step_forward_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowForward))
        self.step_forward_button.setFixedSize(40, 40)
        self.step_forward_button.clicked.connect(self.step_forward)
        self.controls_layout.addWidget(self.step_forward_button)

        self.step_backward_button = QPushButton(self)
        self.step_backward_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowBack))
        self.step_backward_button.setFixedSize(40, 40)
        self.step_backward_button.clicked.connect(self.step_backward)
        self.controls_layout.addWidget(self.step_backward_button)

        self.speed_label = QLabel("Simulation Speed:")
        self.controls_layout.addWidget(self.speed_label)

        self.speed_slider = QSlider(Qt.Horizontal, self)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(1000)
        self.speed_slider.setValue(50)
        self.speed_slider.setFixedWidth(200)
        self.speed_slider.valueChanged.connect(self.update_animation_durations)
        self.controls_layout.addWidget(self.speed_slider)

        self.controls_layout.addStretch()
        self.layout.addLayout(self.controls_layout)

        self.preview_scene = QGraphicsScene(self)
        self.preview_view = QGraphicsView(self.preview_scene, self)
        self.preview_view.setRenderHint(QPainter.Antialiasing)
        self.preview_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.preview_scene.setBackgroundBrush(Qt.black)
        self.preview_view.setMinimumSize(1300, 650)
        self.layout.addWidget(self.preview_view)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_button_blink)
        self.blink_state = False
        self.active_button = None

    def parse_gcode(self, gcode_lines):
        paths = []
        self.gcode_line_indices = []
        current_pos = (0, 0)
        laser_on = False
        for i, line in enumerate(gcode_lines):
            line = line.strip()
            if line.startswith(';') or not line:
                continue
            if line == 'M3':
                laser_on = True
                self.gcode_line_indices.append(i)
                continue
            if line == 'M5':
                laser_on = False
                self.gcode_line_indices.append(i)
                continue
            match = re.match(r'G0\s+X([-]?[\d.]+)\s+Y([-]?[\d.]+)', line)
            if match:
                x, y = float(match.group(1)), float(match.group(2))
                paths.append(("move", current_pos, (x, y)))
                self.gcode_line_indices.append(i)
                current_pos = (x, y)
                continue
            match = re.match(r'G1\s+X([-]?[\d.]+)\s+Y([-]?[\d.]+)', line)
            if match and laser_on:
                x, y = float(match.group(1)), float(match.group(2))
                paths.append(("line", current_pos, (x, y)))
                self.gcode_line_indices.append(i)
                current_pos = (x, y)
        return paths

    def set_simulation_data(self, gcode_lines, worktable_width, worktable_height):
        self.gcode_paths = self.parse_gcode(gcode_lines)
        self.worktable_width = worktable_width
        self.worktable_height = worktable_height
        self.stop_simulation()
        self.draw_paths()

    def draw_paths(self):
        self.preview_scene.clear()
        self.line_items = []
        self.laser_head = None
        self.position_helper = None
        self.min_x, self.min_y = float('inf'), float('inf')
        self.max_x, self.max_y = float('-inf'), float('-inf')

        # لیست‌های جدید برای ذخیره مسیرهای معتبر
        valid_paths = []
        valid_indices = []

        # بررسی و فیلتر کردن مسیرهای نامعتبر (مانند NaN)
        for i, (segment_type, p1, p2) in enumerate(self.gcode_paths):
            x1, y1 = p1[0], p1[1]
            x2, y2 = p2[0], p2[1]
            # چک کردن مقادیر NaN یا نامعتبر
            if math.isnan(x1) or math.isnan(y1) or math.isnan(x2) or math.isnan(y2):
                continue
            # به‌روزرسانی حدود برای مقیاس‌بندی صحنه
            self.min_x = min(self.min_x, x1, x2)
            self.max_x = max(self.max_x, x1, x2)
            self.min_y = min(self.min_y, y1, y2)
            self.max_y = max(self.max_y, y1, y2)
            # ذخیره مسیرهای معتبر
            valid_paths.append((segment_type, p1, p2))
            valid_indices.append(self.gcode_line_indices[i])

        # به‌روزرسانی لیست مسیرها و ایندکس‌ها
        self.gcode_paths = valid_paths
        self.gcode_line_indices = valid_indices

        if not self.gcode_paths:
            self.status_message.emit("No valid G-Code paths for simulation")
            self.preview_scene.setSceneRect(0, 0, 400, 400)
            self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)
            return

        # رسم مسیرها با توجه به اینکه طی‌شده یا نه
        for i, (segment_type, p1, p2) in enumerate(self.gcode_paths):
            x1, y1 = p1[0], p1[1]
            x2, y2 = p2[0], p2[1]
            line = QGraphicsLineItem(x1, y1, x2, y2)
            if i in self.traversed_lines:
                pen = QPen(Qt.red, 1, Qt.SolidLine)  # مسیر طی‌شده
            else:
                if segment_type == "move":
                    pen = QPen(Qt.white, 1, Qt.DashLine)  # خط‌چین برای G0
                else:  # segment_type == "line"
                    pen = QPen(Qt.white, 1, Qt.SolidLine)  # خط معمولی برای G1
            pen.setCosmetic(True)
            line.setPen(pen)
            self.preview_scene.addItem(line)
            self.line_items.append((line, pen.color()))

        # تنظیم حدود صحنه
        if self.min_x == float('inf'):
            self.min_x, self.min_y = 0, 0
            self.max_x, self.max_y = self.worktable_width, self.worktable_height
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        if width == 0 or height == 0:
            width = self.worktable_width
            height = self.worktable_height
        margin = 20
        bounding_rect = QRectF(self.min_x - margin, self.min_y - margin,
                              width + 2 * margin, height + 2 * margin)

        self.preview_scene.setSceneRect(bounding_rect)
        self.fit_view_after_render()

    def fit_view_after_render(self):
        # افزایش تأخیر برای اطمینان از رندر کامل
        QTimer.singleShot(100, lambda: self.preview_view.fitInView(
            self.preview_scene.sceneRect(), Qt.KeepAspectRatio))

    def run_simulation(self):
        if not self.gcode_paths:
            self.status_message.emit("No valid G-Code paths for simulation")
            return
        if self.animations and not self.is_paused:
            self.stop_simulation()
        if self.is_paused:
            self.is_paused = False
            self.is_stepping = False
            if self.current_line_index < len(self.animations):
                self.animations[self.current_line_index].start()
                if self.current_line_index < len(self.gcode_line_indices):
                    self.highlight_gcode_line.emit(self.gcode_line_indices[self.current_line_index])
            self.set_active_button(self.run_button)
            return
        self.current_line_index = 0
        self.traversed_lines.clear()  # پاک کردن مسیرهای طی‌شده
        self.animations = []
        self.is_stepping = False
        self.preview_scene.clear()
        self.line_items = []
        self.laser_head = None
        self.position_helper = None
        self.draw_paths()
        if not self.gcode_paths:
            return
        start_x, start_y = self.gcode_paths[0][1]
        self.laser_head = QGraphicsEllipseItem(-2, -2, 4, 4)
        self.laser_head.setBrush(QBrush(Qt.red))
        self.laser_head.setPen(QPen(Qt.red, 0))
        self.laser_head.setPos(start_x, start_y)
        self.preview_scene.addItem(self.laser_head)
        self.current_position = (start_x, start_y)
        self.position_helper = PositionHelper(self.laser_head, self)
        speed_factor = self.speed_slider.value() / 50.0
        base_duration = 1000 / speed_factor
        for i, (segment_type, p1, p2) in enumerate(self.gcode_paths):
            x1, y1 = p1[0], p1[1]
            x2, y2 = p2[0], p2[1]
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            duration = base_duration * (distance / 100) if distance > 0 else base_duration
            animation = QPropertyAnimation(self.position_helper, b"pos")
            animation.setStartValue(QPointF(x1, y1))
            animation.setEndValue(QPointF(x2, y2))
            animation.setDuration(int(duration))
            if i < len(self.gcode_paths) - 1:
                animation.finished.connect(lambda idx=i: self.on_animation_finished(idx))
            else:
                animation.finished.connect(self.on_simulation_completed)
            self.animations.append(animation)
        if self.animations:
            self.animations[0].start()
            self.set_active_button(self.run_button)
            if len(self.gcode_line_indices) > 0:
                self.highlight_gcode_line.emit(self.gcode_line_indices[0])
        self.preview_view.viewport().update()

    def pause_simulation(self):
        if not self.is_paused:
            self.is_paused = True
            self.is_stepping = False
            if self.current_line_index < len(self.animations):
                self.animations[self.current_line_index].pause()
            self.set_active_button(self.pause_button)

    def stop_simulation(self):
        self.is_paused = False
        self.is_stepping = False
        for animation in self.animations:
            animation.stop()
        self.animations = []
        self.current_line_index = 0
        self.set_active_button(None)
        self.current_position = None
        if self.laser_head and self.laser_head.scene():
            try:
                self.preview_scene.removeItem(self.laser_head)
            except RuntimeError:
                pass
        self.laser_head = None
        self.position_helper = None
        # فقط خطوطی که طی نشده‌اند رو سفید کن
        for i, (line, _) in enumerate(self.line_items):
            if i < len(self.gcode_paths):
                if i not in self.traversed_lines:
                    segment_type = self.gcode_paths[i][0]
                    if segment_type == "move":
                        pen = QPen(Qt.white, 1, Qt.DashLine)
                    else:
                        pen = QPen(Qt.white, 1, Qt.SolidLine)
                    pen.setCosmetic(True)
                    line.setPen(pen)
        self.traversed_lines.clear()  # پاک کردن مسیرهای طی‌شده
        self.highlight_gcode_line.emit(-1)
        self.preview_view.viewport().update()

    def cleanup(self):
        """پاکسازی کامل منابع شبیه‌سازی"""
        self.stop_simulation()
        self.preview_scene.clear()
        self.line_items = []
        self.gcode_paths = []
        self.gcode_line_indices = []
        self.animations = []
        self.preview_scene.setSceneRect(0, 0, 400, 400)
        self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)

    def toggle_button_blink(self):
        self.blink_state = not self.blink_state
        if self.active_button:
            color = "#e8ecef" if self.blink_state else "#ced4da"
            self.active_button.setStyleSheet(f"background-color: {color}; border: 1px solid #adb5bd; padding: 6px; border-radius: 6px;")

    def set_active_button(self, button):
        if self.active_button:
            self.active_button.setStyleSheet("background-color: #e8ecef; border: 1px solid #adb5bd; padding: 6px; border-radius: 6px;")
        self.active_button = button
        if button:
            self.blink_timer.start(500)
        else:
            self.blink_timer.stop()

    def update_animation_durations(self):
        speed_factor = self.speed_slider.value() / 50.0
        base_duration = 1000 / speed_factor
        for i, (segment_type, p1, p2) in enumerate(self.gcode_paths):
            if i < len(self.animations):
                x1, y1 = p1[0], p1[1]
                x2, y2 = p2[0], p2[1]
                distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                duration = base_duration * (distance / 100) if distance > 0 else base_duration
                self.animations[i].setDuration(int(duration))

    def on_animation_finished(self, index):
        self.current_line_index = index + 1
        self.traversed_lines.add(index)  # علامت‌گذاری خط به‌عنوان طی‌شده
        # تغییر رنگ خط طی‌شده به قرمز
        if index < len(self.line_items):
            line, _ = self.line_items[index]
            pen = QPen(Qt.red, 1, Qt.SolidLine)
            pen.setCosmetic(True)
            line.setPen(pen)
        if self.current_line_index < len(self.animations) and not self.is_paused and not self.is_stepping:
            self.animations[self.current_line_index].start()
            if self.current_line_index < len(self.gcode_line_indices):
                self.highlight_gcode_line.emit(self.gcode_line_indices[self.current_line_index])
        self.preview_view.viewport().update()

    def on_simulation_completed(self):
        self.set_active_button(None)
        self.status_message.emit("Simulation completed")
        self.preview_view.viewport().update()

    def step_forward(self):
        if self.current_line_index < len(self.animations):
            self.is_stepping = True
            self.animations[self.current_line_index].start()
            if self.current_line_index < len(self.gcode_line_indices):
                self.highlight_gcode_line.emit(self.gcode_line_indices[self.current_line_index])
            self.traversed_lines.add(self.current_line_index)  # علامت‌گذاری خط به‌عنوان طی‌شده
            if self.current_line_index < len(self.line_items):
                line, _ = self.line_items[self.current_line_index]
                pen = QPen(Qt.red, 1, Qt.SolidLine)
                pen.setCosmetic(True)
                line.setPen(pen)
            self.current_line_index += 1
        self.set_active_button(self.step_forward_button)

    def step_backward(self):
        if self.current_line_index > 0:
            self.current_line_index -= 1
            self.is_stepping = True
            self.traversed_lines.discard(self.current_line_index)  # حذف علامت طی‌شده
            if self.laser_head and self.current_line_index < len(self.gcode_paths):
                x, y = self.gcode_paths[self.current_line_index][1]
                self.laser_head.setPos(x, y)
                if self.current_line_index < len(self.gcode_line_indices):
                    self.highlight_gcode_line.emit(self.gcode_line_indices[self.current_line_index])
            # بازگرداندن رنگ خط به حالت اولیه
            if self.current_line_index < len(self.line_items):
                line, _ = self.line_items[self.current_line_index]
                segment_type = self.gcode_paths[self.current_line_index][0]
                if segment_type == "move":
                    pen = QPen(Qt.white, 1, Qt.DashLine)
                else:
                    pen = QPen(Qt.white, 1, Qt.SolidLine)
                pen.setCosmetic(True)
                line.setPen(pen)
            self.preview_view.viewport().update()
        self.set_active_button(self.step_backward_button)