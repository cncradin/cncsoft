
##################################################################                           بخش ۱ (ابزارها و توابع کمکی)

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QGraphicsScene, QGraphicsView, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsRectItem, QLabel, QLineEdit, QGraphicsTextItem, QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMenuBar, QMenu, QGraphicsItem, QGraphicsItemGroup, QComboBox, QDialogButtonBox, QCheckBox, QSplitter, QSlider, QShortcut, QTextEdit, QGridLayout, QButtonGroup, QTableWidget, QTableWidgetItem, QListWidget, QInputDialog
from PyQt5.QtCore import Qt, QPointF, QRectF, QUrl, QDir, QTimer, QPropertyAnimation, QObject, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QPen, QColor, QPainter, QBrush, QPixmap, QPainterPath, QPainterPathStroker, QIcon, QKeySequence, QTextCharFormat, QTextCursor
from PyQt5.QtCore import QStandardPaths
import ezdxf
import sys
import numpy as np
import math
import json
import os
import re

COLOR_PALETTE = [
    QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255), QColor(255, 255, 0),
    QColor(255, 165, 0), QColor(128, 0, 128), QColor(255, 105, 180), QColor(139, 69, 19),
    QColor(0, 0, 0), QColor(255, 255, 255), QColor(128, 128, 128), QColor(0, 255, 255),
]

def find_closest_color(color):
    r1, g1, b1 = color.red(), color.green(), color.blue()
    min_distance = float('inf')
    closest_color = COLOR_PALETTE[0]
    closest_index = 0
    for i, palette_color in enumerate(COLOR_PALETTE):
        r2, g2, b2 = palette_color.red(), palette_color.green(), palette_color.blue()
        distance = math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
        if distance < min_distance:
            min_distance = distance
            closest_color = palette_color
            closest_index = i
    return closest_color, closest_index

def aci_to_qcolor(aci):
    aci_colors = {
        1: (255, 0, 0), 2: (255, 255, 0), 3: (0, 255, 0), 4: (0, 255, 255),
        5: (0, 0, 255), 6: (255, 0, 255), 7: (255, 255, 255), 8: (128, 128, 128), 9: (192, 192, 192),
    }
    if aci in aci_colors:
        r, g, b = aci_colors[aci]
        color = QColor(r, g, b)
    else:
        if aci == 0 or aci is None:
            color = QColor(0, 0, 0)
        else:
            r = (aci * 37) % 255
            g = (aci * 53) % 255
            b = (aci * 97) % 255
            color = QColor(r, g, b)
    closest_color, closest_index = find_closest_color(color)
    return closest_color, closest_index

class ColorButton(QtWidgets.QPushButton):
    def __init__(self, color, parent=None, main_app=None):
        super().__init__(parent)
        self.color = color
        self.main_app = main_app  # مرجع مستقیم به CNCApp
        self.setFixedSize(30, 30)
        self.setStyleSheet(f"background-color: {self.color.name()}; border: 1px solid #adb5bd; border-radius: 6px;")
        self.clicked.connect(self.on_click)

    def on_click(self):
        if self.main_app:  # چک کردن وجود main_app
            self.main_app.change_selected_items_color(self.color)
        else:
            print("Error: No main application reference available for color change")

class ColorPalette(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)
        # پاس دادن مرجع CNCApp به ColorButton
        for color in COLOR_PALETTE:
            button = ColorButton(color, self, main_app=parent)
            self.layout.addWidget(button)
        self.layout.addStretch()

#######################################################################                                  پایان بخش ۱











#######################################################۲۲۲۲۲۲۲۲۲۲۲۲۲۲۲۲۲                ابتدای رابط کاربری کوچک

class ColorButton(QtWidgets.QPushButton):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(30, 30)
        self.setStyleSheet(f"background-color: {self.color.name()}; border: 1px solid #adb5bd; border-radius: 6px;")
        self.clicked.connect(self.on_click)

    def on_click(self):
        self.parent().parent.change_selected_items_color(self.color)

class ColorPalette(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)
        for color in COLOR_PALETTE:
            button = ColorButton(color, self)
            self.layout.addWidget(button)
        self.layout.addStretch()

class LayerBox(QtWidgets.QWidget):
    layer_hidden_changed = pyqtSignal(QColor, bool)  # سیگنال برای Hide
    layer_output_changed = pyqtSignal(QColor, bool)  # سیگنال برای Output

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layer_label = QtWidgets.QLabel("Layers:")
        self.layout.addWidget(self.layer_label)

        # ایجاد جدول با ۵ ستون (Layer, Mode, Output, Hide, Depth)
        self.layer_table = QtWidgets.QTableWidget(self)
        self.layer_table.setColumnCount(5)
        self.layer_table.setHorizontalHeaderLabels(["Layer", "Mode", "Output", "Hide", "Depth"])
        self.layer_table.setFixedHeight(300)

        # تنظیم عرض ستون‌ها (همه 80 پیکسل)
        self.layer_table.setColumnWidth(0, 80)  # Layer
        self.layer_table.setColumnWidth(1, 80)  # Mode
        self.layer_table.setColumnWidth(2, 80)  # Output
        self.layer_table.setColumnWidth(3, 80)  # Hide
        self.layer_table.setColumnWidth(4, 80)  # Depth
        self.layer_table.horizontalHeader().setStretchLastSection(True)

        # مخفی کردن هدر عمودی
        self.layer_table.verticalHeader().hide()
        self.layer_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        # غیرفعال کردن ویرایش مستقیم سلول‌ها
        self.layer_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # اتصال سیگنال کلیک برای مدیریت چک‌باکس‌ها
        self.layer_table.cellClicked.connect(self.on_cell_clicked)

        # استایل جدول
        self.layer_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #adb5bd;
                background-color: #f0f0f0;
                gridline-color: transparent;
            }
            QHeaderView::section {
                background-color: #e8ecef;
                border: 1px solid #adb5bd;
                padding: 2px;
                font-size: 12px;
            }
            QCheckBox {
                margin-left: 25px;  /* برای وسط‌چین کردن چک‌باکس */
            }
        """)

        self.layout.addWidget(self.layer_table)
        # دیکشنری برای ذخیره وضعیت چک‌باکس‌ها
        self.hide_states = {}  # کلید: رنگ (name)، مقدار: bool
        self.output_states = {}  # کلید: رنگ (name)، مقدار: bool

    def update_layers(self, used_colors):
        # ذخیره وضعیت فعلی چک‌باکس‌ها قبل از بازسازی
        current_hide_states = {}
        current_output_states = {}
        for row in range(self.layer_table.rowCount()):
            color_item = self.layer_table.item(row, 0)
            if color_item:
                color = color_item.background().color().name()
                hide_checkbox = self.layer_table.cellWidget(row, 3)
                output_checkbox = self.layer_table.cellWidget(row, 2)
                if hide_checkbox:
                    current_hide_states[color] = hide_checkbox.isChecked()
                if output_checkbox:
                    current_output_states[color] = output_checkbox.isChecked()

        # بازسازی جدول
        self.layer_table.clearContents()
        self.layer_table.setRowCount(len(used_colors))
        for i, color in enumerate(used_colors):
            color_name = color.name()
            # ستون Layer (رنگ)
            color_item = QtWidgets.QTableWidgetItem("")
            color_item.setBackground(color)
            color_item.setFlags(color_item.flags() & ~Qt.ItemIsEditable)
            self.layer_table.setItem(i, 0, color_item)

            # ستون Mode
            mode_item = QtWidgets.QTableWidgetItem("Laser Cut")
            mode_item.setTextAlignment(Qt.AlignCenter)
            mode_item.setFlags(mode_item.flags() & ~Qt.ItemIsEditable)
            self.layer_table.setItem(i, 1, mode_item)

            # ستون Output (چک‌باکس)
            output_checkbox = QtWidgets.QCheckBox(self)
            # بازیابی وضعیت قبلی یا پیش‌فرض
            output_checkbox.setChecked(current_output_states.get(color_name, True))
            output_checkbox.setProperty("row", i)
            output_checkbox.stateChanged.connect(self.on_output_checkbox_changed)
            self.layer_table.setCellWidget(i, 2, output_checkbox)
            self.output_states[color_name] = output_checkbox.isChecked()

            # ستون Hide (چک‌باکس)
            hide_checkbox = QtWidgets.QCheckBox(self)
            # بازیابی وضعیت قبلی یا پیش‌فرض
            hide_checkbox.setChecked(current_hide_states.get(color_name, False))
            hide_checkbox.setProperty("row", i)
            hide_checkbox.stateChanged.connect(self.on_hide_checkbox_changed)
            self.layer_table.setCellWidget(i, 3, hide_checkbox)
            self.hide_states[color_name] = hide_checkbox.isChecked()

            # ستون Depth
            depth_item = QtWidgets.QTableWidgetItem("0.0")
            depth_item.setTextAlignment(Qt.AlignCenter)
            depth_item.setFlags(depth_item.flags() & ~Qt.ItemIsEditable)
            self.layer_table.setItem(i, 4, depth_item)

            # تنظیم ارتفاع ردیف
            self.layer_table.setRowHeight(i, 20)

    def on_cell_clicked(self, row, column):
        # فقط برای ستون Depth نیاز به دابل‌کلیک داریم
        if column == 4:  # ستون Depth
            color = self.layer_table.item(row, 0).background().color()
            current_depth = self.layer_table.item(row, 4).text()
            depth, ok = QInputDialog.getDouble(self, "Set Depth", f"Enter depth for layer {color.name()} (mm):",
                                               float(current_depth), -100.0, 100.0, 1)
            if ok:
                self.layer_table.item(row, 4).setText(f"{depth:.1f}")

    def on_hide_checkbox_changed(self, state):
        checkbox = self.sender()
        if checkbox:
            row = checkbox.property("row")
            color = self.layer_table.item(row, 0).background().color()
            hide_value = (state == Qt.Checked)
            self.hide_states[color.name()] = hide_value
            self.layer_hidden_changed.emit(color, hide_value)

    def on_output_checkbox_changed(self, state):
        checkbox = self.sender()
        if checkbox:
            row = checkbox.property("row")
            color = self.layer_table.item(row, 0).background().color()
            output_value = (state == Qt.Checked)
            self.output_states[color.name()] = output_value
            self.layer_output_changed.emit(color, output_value)

class PreviewGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.zoom_factor = 1.15
        self.scene().setBackgroundBrush(Qt.black)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def wheelEvent(self, event):
        zoom_in = event.angleDelta().y() > 0
        if zoom_in:
            zoom = self.zoom_factor
        else:
            zoom = 1 / self.zoom_factor
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        mouse_pos = self.mapToScene(event.pos())
        self.scale(zoom, zoom)
        new_pos = self.mapToScene(event.pos())
        delta = new_pos - mouse_pos
        self.translate(delta.x(), delta.y())

    def fit_to_content(self):
        items = self.scene().items()
        if not items:
            return
        bounding_rect = QRectF()
        for item in items:
            if isinstance(item, (QGraphicsLineItem, QGraphicsEllipseItem)):
                item_rect = item.sceneBoundingRect()
                if bounding_rect.isNull():
                    bounding_rect = item_rect
                else:
                    bounding_rect = bounding_rect.united(item_rect)
        if not bounding_rect.isNull():
            margin = 20
            bounding_rect.adjust(-margin, -margin, margin, margin)
            self.fitInView(bounding_rect, Qt.KeepAspectRatio)
        else:
            self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)

class CustomFileDialog(QFileDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select DXF File")
        self.setNameFilter("DXF Files (*.dxf)")
        self.setFileMode(QFileDialog.ExistingFile)
        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.resize(1000, 720)
        sidebar_urls = []
        desktop_paths = QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)
        if desktop_paths:
            sidebar_urls.append(QUrl.fromLocalFile(desktop_paths[0]))
        documents_paths = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
        if documents_paths:
            sidebar_urls.append(QUrl.fromLocalFile(documents_paths[0]))
        home_paths = QStandardPaths.standardLocations(QStandardPaths.HomeLocation)
        if home_paths:
            sidebar_urls.append(QUrl.fromLocalFile(home_paths[0]))
        drives = QDir.drives()
        for drive in drives:
            sidebar_urls.append(QUrl.fromLocalFile(drive.absolutePath()))
        self.setSidebarUrls(sidebar_urls)
        self.preview_scene = QGraphicsScene(self)
        self.preview_view = PreviewGraphicsView(self.preview_scene, self)
        self.preview_view.setMinimumSize(400, 400)
        layout = self.layout()
        if layout is None:
            layout = QVBoxLayout()
            self.setLayout(layout)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        splitter.addWidget(self.preview_view)
        splitter.setSizes([600, 400])
        self.currentChanged.connect(self.update_preview)

    def update_preview(self, path):
        self.preview_scene.clear()
        if not path or not os.path.isfile(path) or not path.lower().endswith('.dxf'):
            self.preview_scene.setSceneRect(0, 0, 400, 400)
            self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)
            return
        try:
            doc = ezdxf.readfile(path)
            msp = doc.modelspace()
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            temp_items = []
            for entity in msp:
                color = aci_to_qcolor(entity.dxf.color)[0] if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'color') else QColor(0, 0, 0)
                if entity.dxftype() == "LINE":
                    x1, y1 = entity.dxf.start.x, -entity.dxf.start.y
                    x2, y2 = entity.dxf.end.x, -entity.dxf.end.y
                    min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                    min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                    line = QGraphicsLineItem(x1, y1, x2, y2)
                    pen = QPen(color, 0)
                    pen.setCosmetic(True)
                    line.setPen(pen)
                    temp_items.append(line)
                elif entity.dxftype() == "SPLINE":
                    points = entity.fit_points if entity.fit_points else list(entity.flattening(distance=0.01))
                    if len(points) >= 2:
                        is_line = all(abs(point[1] - points[0][1]) < 0.01 for point in points)
                        if is_line:
                            x1, y1 = points[0][0], -points[0][1]
                            x2, y2 = points[-1][0], -points[-1][1]
                            min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                            min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                            line = QGraphicsLineItem(x1, y1, x2, y2)
                            pen = QPen(color, 0)
                            pen.setCosmetic(True)
                            line.setPen(pen)
                            temp_items.append(line)
                        else:
                            for i in range(len(points) - 1):
                                x1, y1 = points[i][0], -points[i][1]
                                x2, y2 = points[i + 1][0], -points[i + 1][1]
                                min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                                min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                                line = QGraphicsLineItem(x1, y1, x2, y2)
                                pen = QPen(color, 0)
                                pen.setCosmetic(True)
                                line.setPen(pen)
                                temp_items.append(line)
                elif entity.dxftype() == "LWPOLYLINE":
                    points = entity.get_points()
                    if len(points) >= 2:
                        for i in range(len(points) - 1):
                            x1, y1 = points[i][0], -points[i][1]
                            x2, y2 = points[i + 1][0], -points[i + 1][1]
                            min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                            min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                            line = QGraphicsLineItem(x1, y1, x2, y2)
                            pen = QPen(color, 0)
                            pen.setCosmetic(True)
                            line.setPen(pen)
                            temp_items.append(line)
                        if entity.closed:
                            x1, y1 = points[-1][0], -points[-1][1]
                            x2, y2 = points[0][0], -points[0][1]
                            min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                            min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                            line = QGraphicsLineItem(x1, y1, x2, y2)
                            pen = QPen(color, 0)
                            pen.setCosmetic(True)
                            line.setPen(pen)
                            temp_items.append(line)
                elif entity.dxftype() == "CIRCLE":
                    center_x, center_y = entity.dxf.center.x, -entity.dxf.center.y
                    radius = entity.dxf.radius
                    min_x, max_x = min(min_x, center_x - radius), max(max_x, center_x + radius)
                    min_y, max_y = min(min_y, center_y - radius), max(max_y, center_y + radius)
                    ellipse = QGraphicsEllipseItem(center_x - radius, center_y - radius, 2 * radius, 2 * radius)
                    pen = QPen(color, 0)
                    pen.setCosmetic(True)
                    ellipse.setPen(pen)
                    temp_items.append(ellipse)
                elif entity.dxftype() == "ARC":
                    center_x, center_y = entity.dxf.center.x, -entity.dxf.center.y
                    radius = entity.dxf.radius
                    min_x, max_x = min(min_x, center_x - radius), max(max_x, center_x + radius)
                    min_y, max_y = min(min_y, center_y - radius), max(max_y, center_y + radius)
                    start_angle = math.radians(entity.dxf.start_angle)
                    end_angle = math.radians(entity.dxf.end_angle)
                    if end_angle < start_angle:
                        end_angle += 2 * math.pi
                    num_segments = 36
                    prev_x, prev_y = None, None
                    for i in range(num_segments + 1):
                        t = i / num_segments
                        angle = start_angle + (end_angle - start_angle) * t
                        x = center_x + radius * math.cos(angle)
                        y = center_y + radius * math.sin(angle)
                        if i > 0:
                            line = QGraphicsLineItem(prev_x, prev_y, x, y)
                            pen = QPen(color, 0)
                            pen.setCosmetic(True)
                            line.setPen(pen)
                            temp_items.append(line)
                        prev_x, prev_y = x, y
                elif entity.dxftype() == "ELLIPSE":
                    center_x, center_y = entity.dxf.center.x, -entity.dxf.center.y
                    major_axis = entity.dxf.major_axis
                    ratio = entity.dxf.ratio
                    major_radius = math.sqrt(major_axis[0]**2 + major_axis[1]**2)
                    minor_radius = major_radius * ratio
                    min_x, max_x = min(min_x, center_x - major_radius), max(max_x, center_x + major_radius)
                    min_y, max_y = min(min_y, center_y - minor_radius), max(max_y, center_y + minor_radius)
                    rotation = math.atan2(major_axis[1], major_axis[0])
                    start_angle = entity.dxf.start_angle if hasattr(entity.dxf, 'start_angle') else 0
                    end_angle = entity.dxf.end_angle if hasattr(entity.dxf, 'end_angle') else 2 * math.pi
                    if end_angle < start_angle:
                        end_angle += 2 * math.pi
                    num_segments = 36
                    prev_x, prev_y = None, None
                    for i in range(num_segments + 1):
                        t = i / num_segments
                        angle = start_angle + (end_angle - start_angle) * t
                        x_unrotated = major_radius * math.cos(angle)
                        y_unrotated = minor_radius * math.sin(angle)
                        x = center_x + x_unrotated * math.cos(rotation) - y_unrotated * math.sin(rotation)
                        y = center_y + x_unrotated * math.sin(rotation) + y_unrotated * math.cos(rotation)
                        if i > 0:
                            line = QGraphicsLineItem(prev_x, prev_y, x, y)
                            pen = QPen(color, 0)
                            pen.setCosmetic(True)
                            line.setPen(pen)
                            temp_items.append(line)
                        prev_x, prev_y = x, y
            if min_x != float('inf'):
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                offset_x = -center_x
                offset_y = -center_y
                for item in temp_items:
                    if isinstance(item, QGraphicsLineItem):
                        line = item.line()
                        item.setLine(line.x1() + offset_x, line.y1() + offset_y,
                                     line.x2() + offset_x, line.y2() + offset_y)
                    elif isinstance(item, QGraphicsEllipseItem):
                        rect = item.rect()
                        item.setRect(rect.x() + offset_x, rect.y() + offset_y, rect.width(), rect.height())
                    self.preview_scene.addItem(item)
                width = max_x - min_x
                height = max_y - min_y
                margin = 20
                self.preview_scene.setSceneRect(-width/2 - margin, -height/2 - margin,
                                               width + 2 * margin, height + 2 * margin)
                self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)
            else:
                self.preview_scene.setSceneRect(0, 0, 400, 400)
                self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)
            self.preview_scene.update()
            self.preview_view.viewport().repaint()
        except Exception as e:
            print(f"Error in preview: {str(e)}")
            self.preview_scene.clear()
            self.preview_scene.setSceneRect(0, 0, 400, 400)
            self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.KeepAspectRatio)

class TableConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Table Configuration")
        self.setGeometry(200, 200, 400, 250)
        self.layout = QVBoxLayout(self)
        self.profile_label = QLabel("Table Profile:", self)
        self.layout.addWidget(self.profile_label)
        self.profile_combo = QComboBox(self)
        self.profile_combo.addItems(["Default", "Custom Device 1", "Custom Device 2"])
        self.layout.addWidget(self.profile_combo)
        self.width_label = QLabel("Table Width (mm):", self)
        self.layout.addWidget(self.width_label)
        self.width_input = QLineEdit(str(parent.worktable_width), self)
        self.layout.addWidget(self.width_input)
        self.height_label = QLabel("Table Height (mm):", self)
        self.layout.addWidget(self.height_label)
        self.height_input = QLineEdit(str(parent.worktable_height), self)
        self.layout.addWidget(self.height_input)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.save_settings)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
        self.parent = parent

    def save_settings(self):
        try:
            new_width = float(self.width_input.text())
            new_height = float(self.height_input.text())
            if new_width > 0 and new_height > 0:
                self.parent.worktable_width = new_width
                self.parent.worktable_height = new_height
                self.parent.view.setSceneRect(0, 0, new_width, new_height)
                self.parent.scene.clear()
                self.parent.draw_worktable()
                for path, item in self.parent.graphics_items:
                    self.parent.scene.addItem(item)
                self.parent.view.fitInView(0, 0, new_width, new_height, Qt.KeepAspectRatio)
                self.parent.label.setText("Table size updated successfully")
                settings = {
                    "table_width": new_width,
                    "table_height": new_height,
                    "profile": self.profile_combo.currentText(),
                    "zero_point_corner": self.parent.zero_point_corner
                }
                with open("table_settings.json", "w") as f:
                    json.dump(settings, f)
                self.parent.update_zero_point()
                self.accept()
            else:
                self.parent.label.setText("Table dimensions must be positive")
        except ValueError:
            self.parent.label.setText("Invalid table dimensions")
















######################################################۲۲۲۲۲۲۲۲۲۲۲۲۲۲۲۲                پایان بخش رابط کاربری کوچک (انتهای قسمت ۲)










###############################################        ۳۳۳۳۳۳۳۳۳۳۳۳ابتدای (قسمت ۳) بخش اشیای گرافیکی


class SelectableGraphicsItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, color):
        super().__init__(x1, y1, x2, y2)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.normal_pen = QPen(color, 0)
        self.normal_pen.setCosmetic(True)
        self.setPen(self.normal_pen)
        self.setAcceptHoverEvents(True)

    def shape(self):
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(5)
        return stroker.createStroke(path)

    def paint(self, painter, option, widget=None):
        painter.setPen(self.normal_pen)
        painter.drawLine(self.line())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.scene().update()
            if hasattr(self.scene(), 'parent') and hasattr(self.scene().parent(), 'update_selection_bounding_box'):
                self.scene().parent().update_selection_bounding_box()
        return super().itemChange(change, value)

    def set_normal_color(self, color):
        self.normal_pen = QPen(color, 0)
        self.normal_pen.setCosmetic(True)
        self.setPen(self.normal_pen)
        self.update()

class SelectableEllipseItem(QGraphicsEllipseItem):
    def __init__(self, x, y, w, h, color):
        super().__init__(x, y, w, h)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.normal_pen = QPen(color, 0)
        self.normal_pen.setCosmetic(True)
        self.setPen(self.normal_pen)
        self.setAcceptHoverEvents(True)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.rect())
        stroker = QPainterPathStroker()
        stroker.setWidth(5)
        return stroker.createStroke(path)

    def paint(self, painter, option, widget=None):
        painter.setPen(self.normal_pen)
        painter.drawEllipse(self.rect())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.scene().update()
            if hasattr(self.scene(), 'parent') and hasattr(self.scene().parent(), 'update_selection_bounding_box'):
                self.scene().parent().update_selection_bounding_box()
        return super().itemChange(change, value)

    def set_normal_color(self, color):
        self.normal_pen = QPen(color, 0)
        self.normal_pen.setCosmetic(True)
        self.setPen(self.normal_pen)
        self.update()

class SelectableGroup(QGraphicsItemGroup):
    def __init__(self, color):
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.normal_pen = QPen(color, 0)
        self.normal_pen.setCosmetic(True)
        self.setAcceptHoverEvents(True)

    def shape(self):
        path = QPainterPath()
        for item in self.childItems():
            if isinstance(item, QGraphicsLineItem):
                child_path = QPainterPath()
                child_path.moveTo(item.line().p1())
                child_path.lineTo(item.line().p2())
                path.addPath(child_path)
        stroker = QPainterPathStroker()
        stroker.setWidth(5)
        return stroker.createStroke(path)

    def paint(self, painter, option, widget=None):
        for item in self.childItems():
            if isinstance(item, QGraphicsLineItem):
                painter.setPen(self.normal_pen)
                painter.drawLine(item.line())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.scene().update()
            if hasattr(self.scene(), 'parent') and hasattr(self.scene().parent(), 'update_selection_bounding_box'):
                self.scene().parent().update_selection_bounding_box()
        return super().itemChange(change, value)

    def set_normal_color(self, color):
        self.normal_pen = QPen(color, 0)
        self.normal_pen.setCosmetic(True)
        for item in self.childItems():
            if isinstance(item, QGraphicsLineItem):
                pen = QPen(color, 0)
                pen.setCosmetic(True)
                item.setPen(pen)
        self.update()








###############################################################۳۳۳۳۳۳۳۳۳۳۳۳       پایان (قسمت ۳) بخش اشیای گرافیکی











############################################                   ۴۴۴۴۴۴۴۴۴۴۴۴ابتدای (قسمت ۴) بخش نمایش و تعاملات گرافیکی










class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setMouseTracking(True)
        self.zoom_factor = 1.15
        self.is_panning = False
        self.last_pan_point = QPointF()
        self.parent = parent
        self.is_dragging = False
        self.last_drag_pos = QPointF()
        self.initial_positions = {}
        self.rubber_band_rect = None
        self.rubber_band_start = None

    def wheelEvent(self, event):
        mouse_pos = self.mapToScene(event.pos())
        if hasattr(self.parent, 'update_mouse_position'):
            self.parent.update_mouse_position(mouse_pos.x(), mouse_pos.y())
        zoom_in = event.angleDelta().y() > 0
        zoom = self.zoom_factor if zoom_in else 1 / self.zoom_factor
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.scale(zoom, zoom)
        new_pos = self.mapToScene(event.pos())
        delta = new_pos - mouse_pos
        self.translate(delta.x(), delta.y())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self.is_panning = True
            self.last_pan_point = self.mapToScene(event.pos())
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            items = self.items(event.pos())
            selectable_items = [item for item in items if item.flags() & QGraphicsItem.ItemIsSelectable]
            selected_items = self.scene().selectedItems()
            clicked_on_selected = any(item.boundingRect().translated(item.pos()).contains(scene_pos) for item in selected_items)
            if selectable_items and not clicked_on_selected:
                closest_item = min(selectable_items, key=lambda item: item.boundingRect().width() * item.boundingRect().height(), default=None)
                if closest_item:
                    if not (event.modifiers() & Qt.ShiftModifier):
                        for selected_item in selected_items:
                            selected_item.setSelected(False)
                    closest_item.setSelected(True)
                    self.is_dragging = True
                    self.last_drag_pos = scene_pos
                    self.initial_positions = {item: item.pos() for item in [closest_item] if item.flags() & QGraphicsItem.ItemIsMovable}
            elif clicked_on_selected:
                self.is_dragging = True
                self.last_drag_pos = scene_pos
                self.initial_positions = {item: item.pos() for item in selected_items if item.flags() & QGraphicsItem.ItemIsMovable}
            else:
                if not (event.modifiers() & Qt.ShiftModifier):
                    for selected_item in selected_items:
                        selected_item.setSelected(False)
                self.rubber_band_start = scene_pos
                self.is_dragging = False
                if self.rubber_band_rect:
                    self.scene().removeItem(self.rubber_band_rect)
                self.rubber_band_rect = QGraphicsRectItem()
                pen = QPen(Qt.blue, 0, Qt.DashLine)
                pen.setCosmetic(True)
                self.rubber_band_rect.setPen(pen)
                self.scene().addItem(self.rubber_band_rect)
            self.scene().update()
            self.parent.update_selection_bounding_box()
            self.viewport().update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        mouse_pos = self.mapToScene(event.pos())
        if hasattr(self.parent, 'update_mouse_position'):
            self.parent.update_mouse_position(mouse_pos.x(), mouse_pos.y())
        current_pos = self.mapToScene(event.pos())
        if self.is_panning:
            delta = current_pos - self.last_pan_point
            self.last_pan_point = current_pos
            self.translate(delta.x(), delta.y())
        elif self.is_dragging and hasattr(self, 'last_drag_pos'):
            delta = current_pos - self.last_drag_pos
            self.last_drag_pos = current_pos
            for item in self.scene().selectedItems():
                if item.flags() & QGraphicsItem.ItemIsMovable:
                    item.moveBy(delta.x(), delta.y())
                    item.update()
            self.parent.update_simulation_paths()
            self.parent.update_selection_bounding_box()
        elif self.rubber_band_start is not None:
            min_x = min(self.rubber_band_start.x(), mouse_pos.x())
            min_y = min(self.rubber_band_start.y(), mouse_pos.y())
            max_x = max(self.rubber_band_start.x(), mouse_pos.x())
            max_y = max(self.rubber_band_start.y(), mouse_pos.y())
            self.rubber_band_rect.setRect(min_x, min_y, max_x - min_x, max_y - min_y)
            self.select_items_in_rubber_band(mouse_pos)
        else:
            super().mouseMoveEvent(event)
        self.scene().update()
        self.viewport().update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
        elif event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            moved_items = []
            for item in self.scene().selectedItems():
                if item.flags() & QGraphicsItem.ItemIsMovable and item in self.initial_positions:
                    initial_pos = self.initial_positions[item]
                    final_pos = item.pos()
                    if initial_pos != final_pos:
                        moved_items.append((item, initial_pos, final_pos))
            if moved_items:
                self.parent.add_undo_action({"type": "move", "items": moved_items})
            self.initial_positions = {}
            self.parent.update_selection_bounding_box()
            self.parent.update_zero_point()
            self.parent.data_changed.emit()  # اطلاع‌رسانی تغییر
        elif event.button() == Qt.LeftButton and self.rubber_band_start is not None:
            self.rubber_band_start = None
            if self.rubber_band_rect:
                self.scene().removeItem(self.rubber_band_rect)
                self.rubber_band_rect = None
            self.parent.update_selection_bounding_box()
        else:
            super().mouseReleaseEvent(event)
        self.scene().update()
        self.viewport().update()

    def select_items_in_rubber_band(self, current_pos):
        if self.rubber_band_start is None:
            return
        min_x = min(self.rubber_band_start.x(), current_pos.x())
        min_y = min(self.rubber_band_start.y(), current_pos.y())
        max_x = max(self.rubber_band_start.x(), current_pos.x())
        max_y = max(self.rubber_band_start.y(), current_pos.y())
        rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        items = self.scene().items(rect, Qt.IntersectsItemShape)
        selectable_items = [item for item in items if item.flags() & QGraphicsItem.ItemIsSelectable]
        if not (QApplication.keyboardModifiers() & Qt.ShiftModifier):
            for item in self.scene().selectedItems():
                if item not in selectable_items:
                    item.setSelected(False)
        for item in selectable_items:
            item.setSelected(True)
        self.scene().update()
        self.parent.update_selection_bounding_box()
        self.viewport().update()

class PositionHelper(QObject):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._item = item
        self._pos = item.pos() if item else QPointF(0, 0)

    @pyqtProperty(QPointF)
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        try:
            if self._item and self._item.scene():  # چک کردن اینکه شیء هنوز تو صحنه هست یا نه
                self._item.setPos(value)
        except RuntimeError:
            # شیء حذف شده، پس فقط موقعیت رو ذخیره می‌کنیم و خطا رو نادیده می‌گیریم
            self._item = None
            print("PositionHelper: Attempted to set position on deleted item")
















#######################################################۴۴۴۴۴۴۴۴۴۴۴۴۴۴       پایان (قسمت ۴) بخش نمایش و تعاملات گرافیکی










######################################################۵۵۵۵۵۵۵۵۵۵۵۵۵          ابتدای (قسمت ۵) بخش شبیه سازی






######################################################################۶۶۶۶۶۶۶۶۶۶۶              شروع بخش اصلی برنامه
















######################################################################۶۶۶۶۶۶۶۶۶۶۶              شروع بخش اصلی برنامه

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QLineEdit, QGraphicsScene, QMenuBar, QAction, QGraphicsRectItem, QGraphicsEllipseItem, QShortcut, QGridLayout, QButtonGroup
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QKeySequence
import ezdxf
import json
import os
import numpy as np
import math
from simulation_dialog import SimulationDialog


class CNCApp(QMainWindow):
    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNCSoft")
        self.setGeometry(100, 100, 1700, 900)
        self.paths = []
        self.graphics_items = []
        self.layer_items = {}
        self.used_colors = []
        self.bounding_min_x = 0
        self.bounding_min_y = 0
        self.bounding_max_x = 0
        self.bounding_max_y = 0
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50
        self.gcode_lines = []
        self.selection_bounding_box = None
        self.zero_point = QPointF(0, 0)
        self.zero_point_corner = "top_left"
        self.zero_point_marker = None
        self.hidden_layers = set()
        self.output_off_layers = set()
        self.needs_gcode_update = False
        self.path_cache = {}
        self.update_timer = QTimer(self)  # تایمر برای تأخیر در به‌روزرسانی
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.deferred_update)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)

        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        self.import_action = QAction("Import File", self)
        self.import_action.triggered.connect(self.open_dxf)
        self.file_menu.addAction(self.import_action)
        self.edit_menu = self.menu_bar.addMenu("Edit")
        self.config_menu = self.menu_bar.addMenu("Config")
        self.help_menu = self.menu_bar.addMenu("Help")
        self.table_config_action = QAction("Table Setup", self)
        self.table_config_action.triggered.connect(self.open_table_config)
        self.config_menu.addAction(self.table_config_action)

        button_style = """
            QPushButton {
                background-color: #e8ecef;
                border: 1px solid #adb5bd;
                padding: 6px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:pressed {
                background-color: #ced4da;
                border: 1px solid #6c757d;
            }
        """
        zero_button_style = """
            QPushButton {
                background-color: white;
                border: 1px solid #adb5bd;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: black;
            }
        """

        self.button_layout = QHBoxLayout()
        self.button_gcode = QPushButton("Generate G-Code", self)
        self.button_gcode.setFixedSize(150, 30)
        self.button_gcode.clicked.connect(self.generate_gcode)
        self.button_gcode.setEnabled(False)
        self.button_gcode.setStyleSheet(button_style)
        self.button_gcode.setToolTip("تولید G-Code از مسیرهای قابل‌مشاهده")
        self.button_layout.addWidget(self.button_gcode)

        self.button_delete = QPushButton("Delete Selected", self)
        self.button_delete.setFixedSize(150, 30)
        self.button_delete.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TrashIcon))
        self.button_delete.clicked.connect(self.delete_selected_items)
        self.button_delete.setStyleSheet(button_style)
        self.button_delete.setToolTip("حذف آیتم‌های انتخاب‌شده")
        self.button_layout.addWidget(self.button_delete)

        self.button_undo = QPushButton("Undo", self)
        self.button_undo.setFixedSize(100, 30)
        self.button_undo.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowBack))
        self.button_undo.clicked.connect(self.undo)
        self.button_undo.setStyleSheet(button_style)
        self.button_undo.setToolTip("بازگرداندن آخرین عملیات")
        self.button_layout.addWidget(self.button_undo)

        self.button_redo = QPushButton("Redo", self)
        self.button_redo.setFixedSize(100, 30)
        self.button_redo.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowForward))
        self.button_redo.clicked.connect(self.redo)
        self.button_redo.setStyleSheet(button_style)
        self.button_redo.setToolTip("تکرار آخرین عملیات بازگردانی‌شده")
        self.button_layout.addWidget(self.button_redo)

        self.zero_buttons_layout = QGridLayout()
        self.zero_buttons_layout.setSpacing(5)
        self.zero_button_group = QButtonGroup(self)
        self.zero_button_group.setExclusive(True)

        self.zero_button_top_left = QPushButton(self)
        self.zero_button_top_left.setFixedSize(20, 20)
        self.zero_button_top_left.setCheckable(True)
        self.zero_button_top_left.setStyleSheet(zero_button_style)
        self.zero_button_top_left.clicked.connect(lambda: self.set_zero_point_corner("top_left"))
        self.zero_button_top_left.setToolTip("تنظیم نقطه‌ی صفر در گوشه‌ی بالا-چپ")
        self.zero_buttons_layout.addWidget(self.zero_button_top_left, 0, 0)
        self.zero_button_group.addButton(self.zero_button_top_left)

        self.zero_button_top_right = QPushButton(self)
        self.zero_button_top_right.setFixedSize(20, 20)
        self.zero_button_top_right.setCheckable(True)
        self.zero_button_top_right.setStyleSheet(zero_button_style)
        self.zero_button_top_right.clicked.connect(lambda: self.set_zero_point_corner("top_right"))
        self.zero_button_top_right.setToolTip("تنظیم نقطه‌ی صفر در گوشه‌ی بالا-راست")
        self.zero_buttons_layout.addWidget(self.zero_button_top_right, 0, 1)
        self.zero_button_group.addButton(self.zero_button_top_right)

        self.zero_button_bottom_left = QPushButton(self)
        self.zero_button_bottom_left.setFixedSize(20, 20)
        self.zero_button_bottom_left.setCheckable(True)
        self.zero_button_bottom_left.setStyleSheet(zero_button_style)
        self.zero_button_bottom_left.clicked.connect(lambda: self.set_zero_point_corner("bottom_left"))
        self.zero_button_bottom_left.setToolTip("تنظیم نقطه‌ی صفر در گوشه‌ی پایین-چپ")
        self.zero_buttons_layout.addWidget(self.zero_button_bottom_left, 1, 0)
        self.zero_button_group.addButton(self.zero_button_bottom_left)

        self.zero_button_bottom_right = QPushButton(self)
        self.zero_button_bottom_right.setFixedSize(20, 20)
        self.zero_button_bottom_right.setCheckable(True)
        self.zero_button_bottom_right.setStyleSheet(zero_button_style)
        self.zero_button_bottom_right.clicked.connect(lambda: self.set_zero_point_corner("bottom_right"))
        self.zero_button_bottom_right.setToolTip("تنظیم نقطه‌ی صفر در گوشه‌ی پایین-راست")
        self.zero_buttons_layout.addWidget(self.zero_button_bottom_right, 1, 1)
        self.zero_button_group.addButton(self.zero_button_bottom_right)

        self.button_simulation = QPushButton(self)
        self.button_simulation.setFixedSize(30, 30)
        self.button_simulation.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
        self.button_simulation.clicked.connect(self.open_simulation_window)
        self.button_simulation.setStyleSheet(button_style)
        self.button_simulation.setToolTip("باز کردن پنجره‌ی شبیه‌سازی G-Code")
        self.button_layout.addWidget(self.button_simulation)

        self.button_layout.addLayout(self.zero_buttons_layout)
        self.button_layout.addStretch()
        self.left_layout.addLayout(self.button_layout)

        self.input_layout = QHBoxLayout()
        self.label_speed = QLabel("Speed (F):", self)
        self.input_layout.addWidget(self.label_speed)
        self.input_speed = QLineEdit("500", self)
        self.input_speed.setFixedWidth(60)
        self.input_speed.setToolTip("تنظیم نرخ خوراک (سرعت) برای G-Code")
        self.input_layout.addWidget(self.input_speed)
        self.label_power = QLabel("Power (S):", self)
        self.input_layout.addWidget(self.label_power)
        self.input_power = QLineEdit("1000", self)
        self.input_power.setFixedWidth(60)
        self.input_power.setToolTip("تنظیم قدرت لیزر برای G-Code")
        self.input_layout.addWidget(self.input_power)
        self.input_layout.addStretch()
        self.left_layout.addLayout(self.input_layout)

        self.label = QLabel("هیچ فایلی انتخاب نشده", self)
        self.left_layout.addWidget(self.label)

        self.mouse_layout = QHBoxLayout()
        self.label_mouse_x = QLabel("Mouse X:", self)
        self.mouse_layout.addWidget(self.label_mouse_x)
        self.input_mouse_x = QLineEdit("0", self)
        self.input_mouse_x.setFixedWidth(60)
        self.input_mouse_x.setReadOnly(True)
        self.input_mouse_x.setToolTip("مختصات X ماوس")
        self.mouse_layout.addWidget(self.input_mouse_x)
        self.label_mouse_y = QLabel("Mouse Y:", self)
        self.mouse_layout.addWidget(self.label_mouse_y)
        self.input_mouse_y = QLineEdit("0", self)
        self.input_mouse_y.setFixedWidth(60)
        self.input_mouse_y.setReadOnly(True)
        self.input_mouse_y.setToolTip("مختصات Y ماوس")
        self.mouse_layout.addWidget(self.input_mouse_y)
        self.mouse_layout.addStretch()
        self.left_layout.addLayout(self.mouse_layout)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        self.scene.setParent(self)
        self.view = CustomGraphicsView(self.scene, self)
        self.view.setMinimumSize(1276, 748)
        self.view.setViewportUpdateMode(QtWidgets.QGraphicsView.MinimalViewportUpdate)  # بهینه‌سازی رندرینگ
        self.left_layout.addWidget(self.view)

        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_layout)

        self.layer_box = LayerBox(self)
        self.right_layout.addWidget(self.layer_box)
        self.right_layout.addStretch()

        self.color_palette = ColorPalette(self)
        self.left_layout.addWidget(self.color_palette)

        self.worktable_width = 1300
        self.worktable_height = 900
        if os.path.exists("table_settings.json"):
            try:
                with open("table_settings.json", "r") as f:
                    settings = json.load(f)
                    self.worktable_width = settings.get("table_width", 1300)
                    self.worktable_height = settings.get("table_height", 900)
                    self.zero_point_corner = settings.get("zero_point_corner", "top_left")
            except Exception as e:
                self.label.setText(f"خطا در بارگذاری تنظیمات: {str(e)}")

        if self.zero_point_corner == "top_left":
            self.zero_button_top_left.setChecked(True)
        elif self.zero_point_corner == "top_right":
            self.zero_button_top_right.setChecked(True)
        elif self.zero_point_corner == "bottom_left":
            self.zero_button_bottom_left.setChecked(True)
        elif self.zero_point_corner == "bottom_right":
            self.zero_button_bottom_right.setChecked(True)

        self.view.setSceneRect(0, 0, self.worktable_width, self.worktable_height)
        self.draw_worktable()
        self.update_zero_point()

        self.shortcut_select_all = QShortcut(QKeySequence("Ctrl+A"), self)
        self.shortcut_select_all.activated.connect(self.select_all_items)
        self.shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_delete.activated.connect(self.delete_selected_items)
        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.undo)
        self.shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.shortcut_redo.activated.connect(self.redo)

        self.input_speed.textChanged.connect(self.on_speed_power_changed)
        self.input_power.textChanged.connect(self.on_speed_power_changed)
        self.layer_box.layer_hidden_changed.connect(self.toggle_layer_visibility)
        self.layer_box.layer_output_changed.connect(self.toggle_layer_output)

    def on_speed_power_changed(self):
        self.needs_gcode_update = True
        self.schedule_update()

    def update_status_label(self, message):
        self.label.setText(message)

    def open_simulation_window(self):
        if self.needs_gcode_update or not self.gcode_lines:
            self.generate_gcode()
        if not self.gcode_lines:
            self.label.setText("هیچ G-Code‌ای برای شبیه‌سازی موجود نیست")
            return
        dialog = SimulationDialog(self, self.gcode_lines, self.worktable_width, self.worktable_height)
        dialog.finished.connect(self.on_simulation_closed)
        dialog.exec_()

    def on_simulation_closed(self):
        self.path_cache.clear()
        self.schedule_update()

    def schedule_update(self):
        if not self.update_timer.isActive():
            self.update_timer.start(100)

    def deferred_update(self):
        self.update_simulation_paths()
        self.scene.update()
        self.view.viewport().update()

    def calculate_objects_bounding_box(self):
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        for _, item in self.graphics_items:
            if not item.isVisible():
                continue
            rect = item.boundingRect().translated(item.pos())
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())
        if min_x == float('inf'):
            return 0, 0, self.worktable_width, self.worktable_height
        return min_x, min_y, max_x, max_y

    def set_zero_point_corner(self, corner):
        self.zero_point_corner = corner
        self.update_zero_point()
        self.needs_gcode_update = True
        self.label.setText(f"نقطه‌ی صفر تنظیم شد به {corner.replace('_', ' ')}")
        settings = {
            "table_width": self.worktable_width,
            "table_height": self.worktable_height,
            "profile": "Default",
            "zero_point_corner": self.zero_point_corner
        }
        try:
            with open("table_settings.json", "w") as f:
                json.dump(settings, f)
        except Exception as e:
            self.label.setText(f"خطا در ذخیره‌ی نقطه‌ی صفر: {str(e)}")
        self.schedule_update()

    def update_zero_point(self):
        if self.zero_point_marker and self.zero_point_marker.scene() == self.scene:
            self.scene.removeItem(self.zero_point_marker)
        self.zero_point_marker = None
        min_x, min_y, max_x, max_y = self.calculate_objects_bounding_box()
        if self.zero_point_corner == "top_left":
            self.zero_point = QPointF(min_x, min_y)
        elif self.zero_point_corner == "top_right":
            self.zero_point = QPointF(max_x, min_y)
        elif self.zero_point_corner == "bottom_left":
            self.zero_point = QPointF(min_x, max_y)
        else:
            self.zero_point = QPointF(max_x, max_y)
        marker_size = 5
        self.zero_point_marker = QGraphicsEllipseItem(
            self.zero_point.x() - marker_size / 2,
            self.zero_point.y() - marker_size / 2,
            marker_size, marker_size
        )
        self.zero_point_marker.setBrush(QBrush(Qt.red))
        self.zero_point_marker.setPen(QPen(Qt.NoPen))
        self.zero_point_marker.setZValue(100)
        self.scene.addItem(self.zero_point_marker)

    def update_selection_bounding_box(self):
        if self.selection_bounding_box:
            self.scene.removeItem(self.selection_bounding_box)
            self.selection_bounding_box = None
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        for item in selected_items:
            if not item.isVisible():
                continue
            rect = item.boundingRect().translated(item.pos())
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())
        if min_x != float('inf'):
            self.selection_bounding_box = QGraphicsRectItem(min_x - 2, min_y - 2, max_x - min_x + 4, max_y - min_y + 4)
            pen = QPen(Qt.red, 0, Qt.DashLine)
            pen.setCosmetic(True)
            self.selection_bounding_box.setPen(pen)
            self.scene.addItem(self.selection_bounding_box)

    def add_undo_action(self, action):
        self.undo_stack.append(action)
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def select_all_items(self):
        for item in self.scene.items():
            if isinstance(item, (SelectableGraphicsItem, SelectableEllipseItem, SelectableGroup)) and item.isVisible():
                item.setSelected(True)
        self.update_selection_bounding_box()
        self.label.setText("همه‌ی آیتم‌های قابل‌مشاهده انتخاب شدند")
        self.schedule_update()

    def delete_selected_items(self):
        selected_items = self.scene.selectedItems()
        if not selected_items:
            self.label.setText("هیچ آیتمی برای حذف انتخاب نشده")
            return
        deleted_items = []
        for item in selected_items:
            if isinstance(item, (SelectableGraphicsItem, SelectableEllipseItem, SelectableGroup)):
                for path, graphics_item in self.graphics_items:
                    if graphics_item == item:
                        deleted_items.append((path, graphics_item))
                        self.paths.remove(path)
                        self.graphics_items.remove((path, graphics_item))
                        color_name = graphics_item.normal_pen.color().name()
                        if color_name in self.layer_items:
                            self.layer_items[color_name] = [(p, i) for p, i in self.layer_items[color_name] if i != graphics_item]
                            if not self.layer_items[color_name]:
                                del self.layer_items[color_name]
                        if id(item) in self.path_cache:
                            del self.path_cache[id(item)]
                        break
                self.scene.removeItem(item)
        if deleted_items:
            self.add_undo_action({"type": "delete", "items": deleted_items})
            self.update_used_colors()
            self.label.setText(f"{len(deleted_items)} آیتم حذف شدند")
            self.update_zero_point()
            self.needs_gcode_update = True
            self.schedule_update()
        else:
            self.label.setText("هیچ آیتم معتبری برای حذف وجود ندارد")
        self.update_selection_bounding_box()

    def undo(self):
        if not self.undo_stack:
            self.label.setText("هیچ عملیاتی برای بازگرداندن وجود ندارد")
            return
        action = self.undo_stack.pop()
        if action["type"] == "delete":
            deleted_items = action["items"]
            for path, item in deleted_items:
                self.paths.append(path)
                self.graphics_items.append((path, item))
                color_name = item.normal_pen.color().name()
                if color_name not in self.layer_items:
                    self.layer_items[color_name] = []
                self.layer_items[color_name].append((path, item))
                item.setVisible(color_name not in self.hidden_layers)
                self.scene.addItem(item)
            self.redo_stack.append(action)
            self.update_used_colors()
            self.label.setText(f"{len(deleted_items)} آیتم بازگردانی شدند")
            self.update_zero_point()
        elif action["type"] == "move":
            moved_items = action["items"]
            for item, initial_pos, final_pos in moved_items:
                item.setPos(initial_pos)
                item.setVisible(item.normal_pen.color().name() not in self.hidden_layers)
                if id(item) in self.path_cache:
                    del self.path_cache[id(item)]
            self.redo_stack.append(action)
            self.label.setText(f"جابه‌جایی {len(moved_items)} آیتم بازگردانی شد")
            self.update_zero_point()
        elif action["type"] == "color_change":
            changed_items = action["items"]
            for item, old_color, new_color in changed_items:
                old_color_name = old_color.name()
                new_color_name = new_color.name()
                if new_color_name in self.layer_items:
                    self.layer_items[new_color_name] = [(p, i) for p, i in self.layer_items[new_color_name] if i != item]
                    if not self.layer_items[new_color_name]:
                        del self.layer_items[new_color_name]
                if old_color_name not in self.layer_items:
                    self.layer_items[old_color_name] = []
                self.layer_items[old_color_name].append((item.path, item))
                item.set_normal_color(old_color)
                item.setVisible(old_color_name not in self.hidden_layers)
                if id(item) in self.path_cache:
                    del self.path_cache[id(item)]
            self.redo_stack.append(action)
            self.update_used_colors()
            self.label.setText(f"تغییر رنگ {len(changed_items)} آیتم بازگردانی شد")
        self.needs_gcode_update = True
        self.schedule_update()

    def redo(self):
        if not self.redo_stack:
            self.label.setText("هیچ عملیاتی برای تکرار وجود ندارد")
            return
        action = self.redo_stack.pop()
        if action["type"] == "delete":
            deleted_items = action["items"]
            for path, item in deleted_items:
                self.paths.remove(path)
                self.graphics_items.remove((path, item))
                color_name = item.normal_pen.color().name()
                if color_name in self.layer_items:
                    self.layer_items[color_name] = [(p, i) for p, i in self.layer_items[color_name] if i != item]
                    if not self.layer_items[color_name]:
                        del self.layer_items[color_name]
                if id(item) in self.path_cache:
                    del self.path_cache[id(item)]
                self.scene.removeItem(item)
            self.undo_stack.append(action)
            self.update_used_colors()
            self.label.setText(f"{len(deleted_items)} آیتم دوباره حذف شدند")
            self.update_zero_point()
        elif action["type"] == "move":
            moved_items = action["items"]
            for item, initial_pos, final_pos in moved_items:
                item.setPos(final_pos)
                item.setVisible(item.normal_pen.color().name() not in self.hidden_layers)
                if id(item) in self.path_cache:
                    del self.path_cache[id(item)]
            self.undo_stack.append(action)
            self.label.setText(f"جابه‌جایی {len(moved_items)} آیتم تکرار شد")
            self.update_zero_point()
        elif action["type"] == "color_change":
            changed_items = action["items"]
            for item, old_color, new_color in changed_items:
                old_color_name = old_color.name()
                new_color_name = new_color.name()
                if old_color_name in self.layer_items:
                    self.layer_items[old_color_name] = [(p, i) for p, i in self.layer_items[old_color_name] if i != item]
                    if not self.layer_items[old_color_name]:
                        del self.layer_items[old_color_name]
                if new_color_name not in self.layer_items:
                    self.layer_items[new_color_name] = []
                self.layer_items[new_color_name].append((item.path, item))
                item.set_normal_color(new_color)
                item.setVisible(new_color_name not in self.hidden_layers)
                if id(item) in self.path_cache:
                    del self.path_cache[id(item)]
            self.undo_stack.append(action)
            self.update_used_colors()
            self.label.setText(f"تغییر رنگ {len(changed_items)} آیتم تکرار شد")
        self.needs_gcode_update = True
        self.schedule_update()

    def update_used_colors(self):
        self.used_colors = []
        for item in self.scene.items():
            if isinstance(item, (SelectableGraphicsItem, SelectableEllipseItem, SelectableGroup)):
                color = item.normal_pen.color()
                _, color_index = find_closest_color(color)
                if (color, color_index) not in self.used_colors:
                    self.used_colors.append((color, color_index))
        self.used_colors.sort(key=lambda x: x[1])
        used_colors_only = [color for color, _ in self.used_colors]
        self.layer_box.update_layers(used_colors_only)

    def open_table_config(self):
        dialog = TableConfigDialog(self)
        dialog.exec_()

    def change_selected_items_color(self, new_color):
        try:
            selected_items = self.scene.selectedItems()
            if not selected_items:
                self.label.setText("هیچ آیتمی برای تغییر رنگ انتخاب نشده")
                return
            _, new_color_index = find_closest_color(new_color)
            changed_items = []
            for item in selected_items:
                if isinstance(item, (SelectableGraphicsItem, SelectableEllipseItem, SelectableGroup)):
                    old_color = item.normal_pen.color()
                    old_color_name = old_color.name()
                    new_color_name = new_color.name()
                    if old_color_name in self.layer_items:
                        self.layer_items[old_color_name] = [(p, i) for p, i in self.layer_items[old_color_name] if i != item]
                        if not self.layer_items[old_color_name]:
                            del self.layer_items[old_color_name]
                    if new_color_name not in self.layer_items:
                        self.layer_items[new_color_name] = []
                    self.layer_items[new_color_name].append((item.path, item))
                    item.set_normal_color(new_color)
                    item.setVisible(new_color_name not in self.hidden_layers)
                    changed_items.append((item, old_color, new_color))
                    if id(item) in self.path_cache:
                        del self.path_cache[id(item)]
            if changed_items:
                self.add_undo_action({"type": "color_change", "items": changed_items})
                self.update_used_colors()
                self.label.setText(f"رنگ {len(changed_items)} آیتم تغییر کرد")
            else:
                self.label.setText("هیچ آیتم معتبری برای تغییر رنگ وجود ندارد")
            self.update_selection_bounding_box()
            self.needs_gcode_update = True
            self.schedule_update()
        except Exception as e:
            self.label.setText(f"خطا در تغییر رنگ: {str(e)}")
            print(f"خطا در change_selected_items_color: {str(e)}")

    def update_mouse_position(self, x, y):
        self.input_mouse_x.setText(f"{x:.2f}")
        self.input_mouse_y.setText(f"{y:.2f}")

    def draw_worktable(self):
        grid_step = 100
        for x in range(0, int(self.worktable_width) + 1, grid_step):
            line = QGraphicsLineItem(x, 0, x, self.worktable_height)
            line.setPen(Qt.lightGray)
            self.scene.addItem(line)
            label = QGraphicsTextItem(str(x))
            label.setPos(x - 10, self.worktable_height - 20)
            self.scene.addItem(label)
        for y in range(0, int(self.worktable_height) + 1, grid_step):
            line = QGraphicsLineItem(0, y, self.worktable_width, y)
            line.setPen(Qt.lightGray)
            self.scene.addItem(line)
            label = QGraphicsTextItem(str(self.worktable_height - y))
            label.setPos(-30, y - 5)
            self.scene.addItem(label)
        border = QGraphicsLineItem(0, 0, self.worktable_width, 0)
        border.setPen(Qt.black)
        self.scene.addItem(border)
        border = QGraphicsLineItem(0, self.worktable_height, self.worktable_width, self.worktable_height)
        border.setPen(Qt.black)
        self.scene.addItem(border)
        border = QGraphicsLineItem(0, 0, 0, self.worktable_height)
        border.setPen(Qt.black)
        self.scene.addItem(border)
        border = QGraphicsLineItem(self.worktable_width, 0, self.worktable_width, self.worktable_height)
        border.setPen(Qt.black)
        self.scene.addItem(border)

    def toggle_layer_visibility(self, color, hide):
        color_name = color.name()
        if hide:
            self.hidden_layers.add(color_name)
        else:
            self.hidden_layers.discard(color_name)
        if color_name in self.layer_items:
            for _, item in self.layer_items[color_name]:
                item.setVisible(not hide)
                if id(item) in self.path_cache:
                    del self.path_cache[id(item)]
        self.update_selection_bounding_box()
        self.update_zero_point()
        self.needs_gcode_update = True
        self.label.setText(f"لایه برای رنگ {color_name} {'مخفی' if hide else 'نمایش داده'} شد")
        self.schedule_update()

    def toggle_layer_output(self, color, output_enabled):
        color_name = color.name()
        if not output_enabled:
            self.output_off_layers.add(color_name)
        else:
            self.output_off_layers.discard(color_name)
        self.label.setText(f"اوت‌پوت برای رنگ {color_name} {'غیرفعال' if not output_enabled else 'فعال'} شد")
        self.needs_gcode_update = True
        if color_name in self.layer_items:
            for _, item in self.layer_items[color_name]:
                if id(item) in self.path_cache:
                    del self.path_cache[id(item)]
        self.schedule_update()

    def open_dxf(self):
        dialog = CustomFileDialog(self)
        if dialog.exec_():
            file_path = dialog.selectedFiles()[0]
            try:
                doc = ezdxf.readfile(file_path)
                msp = doc.modelspace()
                self.paths = []
                self.graphics_items = []
                self.layer_items = {}
                self.used_colors = []
                self.undo_stack = []
                self.redo_stack = []
                self.gcode_lines = []
                self.hidden_layers = set()
                self.output_off_layers = set()
                self.path_cache = {}
                self.needs_gcode_update = False
                self.scene.clear()
                self.zero_point_marker = None
                self.draw_worktable()
                min_x, min_y = float('inf'), float('inf')
                max_x, max_y = float('-inf'), float('-inf')
                temp_paths = []
                temp_items = []
                for entity in msp:
                    color = None
                    if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'color'):
                        color, _ = aci_to_qcolor(entity.dxf.color)
                    if color is None and hasattr(entity, 'dxf') and hasattr(entity.dxf, 'layer'):
                        layer_name = entity.dxf.layer
                        layer = doc.layers.get(layer_name)
                        if layer and hasattr(layer, 'color'):
                            color, _ = aci_to_qcolor(layer.color)
                    if color is None:
                        color = QColor(0, 0, 0)
                    color_index = find_closest_color(color)[1]
                    if (color, color_index) not in self.used_colors:
                        self.used_colors.append((color, color_index))
                    if entity.dxftype() == "LINE":
                        x1, y1 = entity.dxf.start.x, -entity.dxf.start.y
                        x2, y2 = entity.dxf.end.x, -entity.dxf.end.y
                        min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                        min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                        path = [("line", (x1, y1), (x2, y2))]
                        line = SelectableGraphicsItem(x1, y1, x2, y2, color)
                        line.path = path
                        line.setVisible(color.name() not in self.hidden_layers)
                        temp_paths.append(path)
                        temp_items.append((path, line))
                    elif entity.dxftype() == "SPLINE":
                        points = entity.fit_points if entity.fit_points else list(entity.flattening(distance=0.01))
                        if len(points) >= 2:
                            is_line = all(abs(point[1] - points[0][1]) < 0.01 for point in points)
                            path = []
                            group = SelectableGroup(color)
                            group.setVisible(color.name() not in self.hidden_layers)
                            if is_line:
                                x1, y1 = points[0][0], -points[0][1]
                                x2, y2 = points[-1][0], -points[-1][1]
                                min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                                min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                                path = [("line", (x1, y1), (x2, y2))]
                                line = QGraphicsLineItem(x1, y1, x2, y2)
                                pen = QPen(color, 0)
                                pen.setCosmetic(True)
                                line.setPen(pen)
                                group.addToGroup(line)
                            else:
                                for i in range(len(points) - 1):
                                    x1, y1 = points[i][0], -points[i][1]
                                    x2, y2 = points[i + 1][0], -points[i + 1][1]
                                    min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                                    min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                                    path.append(("line", (x1, y1), (x2, y2)))
                                    line = QGraphicsLineItem(x1, y1, x2, y2)
                                    pen = QPen(color, 0)
                                    pen.setCosmetic(True)
                                    line.setPen(pen)
                                    group.addToGroup(line)
                            group.path = path
                            temp_paths.append(path)
                            temp_items.append((path, group))
                    elif entity.dxftype() == "LWPOLYLINE":
                        points = entity.get_points()
                        if len(points) >= 2:
                            path = []
                            group = SelectableGroup(color)
                            group.setVisible(color.name() not in self.hidden_layers)
                            for i in range(len(points) - 1):
                                x1, y1 = points[i][0], -points[i][1]
                                x2, y2 = points[i + 1][0], -points[i + 1][1]
                                min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                                min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                                path.append(("line", (x1, y1), (x2, y2)))
                                line = QGraphicsLineItem(x1, y1, x2, y2)
                                pen = QPen(color, 0)
                                pen.setCosmetic(True)
                                line.setPen(pen)
                                group.addToGroup(line)
                            if entity.closed:
                                x1, y1 = points[-1][0], -points[-1][1]
                                x2, y2 = points[0][0], -points[0][1]
                                min_x, max_x = min(min_x, x1, x2), max(max_x, x1, x2)
                                min_y, max_y = min(min_y, y1, y2), max(max_y, y1, y2)
                                path.append(("line", (x1, y1), (x2, y2)))
                                line = QGraphicsLineItem(x1, y1, x2, y2)
                                pen = QPen(color, 0)
                                pen.setCosmetic(True)
                                line.setPen(pen)
                                group.addToGroup(line)
                            group.path = path
                            temp_paths.append(path)
                            temp_items.append((path, group))
                    elif entity.dxftype() == "CIRCLE":
                        center_x, center_y = entity.dxf.center.x, -entity.dxf.center.y
                        radius = entity.dxf.radius
                        min_x, max_x = min(min_x, center_x - radius), max(max_x, center_x + radius)
                        min_y, max_y = min(min_y, center_y - radius), max(max_y, center_y + radius)
                        ellipse = SelectableEllipseItem(center_x - radius, center_y - radius, 2 * radius, 2 * radius, color)
                        ellipse.setVisible(color.name() not in self.hidden_layers)
                        num_segments = 36
                        path = []
                        for i in range(num_segments):
                            angle1 = 2 * np.pi * i / num_segments
                            angle2 = 2 * np.pi * (i + 1) / num_segments
                            x1 = center_x + radius * np.cos(angle1)
                            y1 = center_y + radius * np.sin(angle1)
                            x2 = center_x + radius * np.cos(angle2)
                            y2 = center_y + radius * np.sin(angle2)
                            path.append(("line", (x1, y1), (x2, y2)))
                        ellipse.path = path
                        temp_paths.append(path)
                        temp_items.append((path, ellipse))
                    elif entity.dxftype() == "ARC":
                        center_x, center_y = entity.dxf.center.x, -entity.dxf.center.y
                        radius = entity.dxf.radius
                        start_angle = math.radians(entity.dxf.start_angle)
                        end_angle = math.radians(entity.dxf.end_angle)
                        if end_angle < start_angle:
                            end_angle += 2 * math.pi
                        num_segments = 36
                        path = []
                        group = SelectableGroup(color)
                        group.setVisible(color.name() not in self.hidden_layers)
                        prev_x, prev_y = None, None
                        for i in range(num_segments + 1):
                            t = i / num_segments
                            angle = start_angle + (end_angle - start_angle) * t
                            x = center_x + radius * math.cos(angle)
                            y = center_y + radius * math.sin(angle)
                            if i > 0:
                                path.append(("line", (prev_x, prev_y), (x, y)))
                                line = QGraphicsLineItem(prev_x, prev_y, x, y)
                                pen = QPen(color, 0)
                                pen.setCosmetic(True)
                                line.setPen(pen)
                                group.addToGroup(line)
                            prev_x, prev_y = x, y
                        group.path = path
                        min_x, max_x = min(min_x, center_x - radius), max(max_x, center_x + radius)
                        min_y, max_y = min(min_y, center_y - radius), max(max_y, center_y + radius)
                        temp_paths.append(path)
                        temp_items.append((path, group))
                    elif entity.dxftype() == "ELLIPSE":
                        center_x, center_y = entity.dxf.center.x, -entity.dxf.center.y
                        major_axis = entity.dxf.major_axis
                        ratio = entity.dxf.ratio
                        major_radius = math.sqrt(major_axis[0]**2 + major_axis[1]**2)
                        minor_radius = major_radius * ratio
                        rotation = math.atan2(major_axis[1], major_axis[0])
                        start_angle = entity.dxf.start_angle if hasattr(entity.dxf, 'start_angle') else 0
                        end_angle = entity.dxf.end_angle if hasattr(entity.dxf, 'end_angle') else 2 * math.pi
                        if end_angle < start_angle:
                            end_angle += 2 * math.pi
                        num_segments = 36
                        path = []
                        group = SelectableGroup(color)
                        group.setVisible(color.name() not in self.hidden_layers)
                        prev_x, prev_y = None, None
                        for i in range(num_segments + 1):
                            t = i / num_segments
                            angle = start_angle + (end_angle - start_angle) * t
                            x_unrotated = major_radius * math.cos(angle)
                            y_unrotated = minor_radius * math.sin(angle)
                            x = center_x + x_unrotated * math.cos(rotation) - y_unrotated * math.sin(rotation)
                            y = center_y + x_unrotated * math.sin(rotation) + y_unrotated * math.cos(rotation)
                            if i > 0:
                                path.append(("line", (prev_x, prev_y), (x, y)))
                                line = QGraphicsLineItem(prev_x, prev_y, x, y)
                                pen = QPen(color, 0)
                                pen.setPen(pen)
                                line.setPen(pen)
                                group.addToGroup(line)
                            prev_x, prev_y = x, y
                        group.path = path
                        min_x, max_x = min(min_x, center_x - major_radius), max(max_x, center_x + major_radius)
                        min_y, max_y = min(min_y, center_y - minor_radius), max(max_y, center_y - minor_radius)
                        temp_paths.append(path)
                        temp_items.append(path, group)
                for path, item in temp_items:
                    self.paths.append(path)
                    self.graphics_items.append((path, item))
                    color_name = item.normal_pen.color().name()
                    if color_name not in self.layer_items:
                        self.layer_items[color_name] = []
                    self.layer_items[color_name].append((path, item))
                    self.scene.addItem(item)
                self.bounding_min_x = min_x if min_x != float('inf') else 0
                self.bounding_max_x = max_x if max_x != float('-inf') else self.worktable_width
                self.bounding_min_y = max_y if max_y != float('-inf') else self.worktable_height
                self.bounding_max_y = min_y if min_y != float('inf') else 0
                center_x = (self.bounding_min_x + self.bounding_max_x) / 2
                center_y = (self.bounding_min_y + self.bounding_max_y) / 2
                offset_x = self.worktable_width / 2 - center_x
                offset_y = self.worktable_height /  2 - center_y
                for _, item in self.graphics_items:
                    item.moveBy(offset_x, offset_y)
                self.update_used_colors()
                self.label.setText(f"فایل DXF با موفقیت بارگذاری شد: {os.path.basename(file_path)}")
                self.button_gcode.setEnabled(True)
                self.update_zero_point()
                self.view.fitInView(0, 0, self.worktable_width, self.worktable_height, Qt.KeepAspectRatio)
            except PermissionError as e:
                self.label.setText(f"خطا در بارگذاری فایل DXF: عدم دسترسی - {str(e)}")
            except FileNotFoundError as e:
                self.label.setText(f"خطا در بارگذاری فایل DXF: فایل یافت نشد - {str(e)}")
            except Exception as e:
                self.label.setText(f"خطا در بارگذاری فایل DXF: {str(e)}")

    def find_closest_point(self, zero_x, zero_y):
        min_distance = float('inf')
        closest_point = None
        closest_path_index = None
        for i, (path, item) in enumerate(self.graphics_items):
            if not item.isVisible() or item.normal_pen.color().name() in self.output_off_layers:
                continue
            for segment_type, p1, p2 in path:
                for point in [p1, p2]:
                    x, y = point
                    offset = item.pos()
                    x += offset.x() - zero_x
                    y += offset.y() - zero_y
                    distance = math.sqrt(x**2 + y**2)
                    if distance < min_distance:
                        min_distance = distance
                        closest_point = (x, y)
                        closest_path_index = i
                return closest_point, closest_path_index

    def generate_gcode(self):
        visible_paths = []
        path_indices = []
        for i, (path, item) in enumerate(self.graphics_items):
            if item.isVisible() and item.normal_pen.color().name() not in self.output_off_layers:
                visible_paths.append(path)
                path_indices.append(i)

        if not visible_paths:
            self.label.setText("هیچ مسیر قابل‌مشاهده‌ای برای تولید G-Code وجود ندارد")
            self.gcode_lines = []
            self.needs_gcode_update = False
            return

        try:
            speed = float(self.input_speed.text())
            power = float(self.input_power.text())
            if speed <= 0 or power <= 0:
                self.label.setText("سرعت و قدرت باید مثبت باشند")
                self.gcode_lines = []
                self.needs_gcode_update = False
                return
        except ValueError:
            self.label.setText("مقدار سرعت یا قدرت نامعتبر است")
            self.gcode_lines = []
            self.needs_gcode_update = False
            return

        self.gcode_lines = []
        self.gcode_lines.append("; G-Code تولیدشده توسط CNCSoft")
        self.gcode_lines.append("G90")
        self.gcode_lines.append("G21")
        self.gcode_lines.append(f"F{speed}")
        zero_x, zero_y = self.zero_point.x(), self.zero_point.y()
        closest_point, closest_path_index = self.find_closest_point(zero_x, zero_y)
        if closest_point is None or closest_path_index is None:
            self.label.setText("هیچ نقطه‌ی معتبری برای G-Code یافت نشد")
            self.gcode_lines = []
            self.needs_gcode_update = False
            return

        current_pos = closest_point
        self.gcode_lines.append("M5")
        self.gcode_lines.append(f"G0 X{current_pos[0]:.3f} Y{current_pos[1]:.3f}")

        processed_paths = set()
        if closest_path_index in path_indices:
            closest_visible_index = path_indices.index(closest_path_index)
            processed_paths.add(closest_visible_index)
            path = visible_paths[closest_visible_index]
            for segment_type, p1, p2 in path:
                x1, y1 = p1
                x2, y2 = p2
                offset = QPointF(0, 0)
                for p, item in self.graphics_items:
                    if p == path and item.isVisible():
                        offset = item.pos()
                        break
                x1 += offset.x() - zero_x
                y1 += offset.y() - zero_y
                x2 += offset.x() - zero_x
                y2 += offset.y() - zero_y
                if current_pos != (x1, y1):
                    self.gcode_lines.append("M5")
                    self.gcode_lines.append(f"G0 X{x1:.3f} Y{y1:.3f}")
                    current_pos = (x1, y1)
                self.gcode_lines.append("M3")
                self.gcode_lines.append(f"G1 X{x2:.3f} Y{y2:.3f} S{power}")
                current_pos = (x2, y2)

        while len(processed_paths) < len(visible_paths):
            min_distance = float('inf')
            next_path_index = None
            next_start_point = None
            for i, path in enumerate(visible_paths):
                if i in processed_paths:
                    continue
                for segment_type, p1, p2 in path:
                    x1, y1 = p1
                    offset = QPointF(0, 0)
                    for p, item in self.graphics_items:
                        if p == path and item.isVisible():
                            offset = item.pos()
                            break
                    x1 += offset.x() - zero_x
                    y1 += offset.y() - zero_y
                    distance = math.sqrt((x1 - current_pos[0])**2 + (y1 - current_pos[1])**2)
                    if distance < min_distance:
                        min_distance = distance
                        next_path_index = i
                        next_start_point = (x1, y1)
            if next_path_index is None:
                break
            processed_paths.add(next_path_index)
            path = visible_paths[next_path_index]
            self.gcode_lines.append("M5")
            self.gcode_lines.append(f"G0 X{next_start_point[0]:.3f} Y{next_start_point[1]:.3f}")
            current_pos = next_start_point
            for segment_type, p1, p2 in path:
                x1, y1 = p1
                x2, y2 = p2
                offset = QPointF(0, 0)
                for p, item in self.graphics_items:
                    if p == path and item.isVisible():
                        offset = item.pos()
                        break
                x1 += offset.x() - zero_x
                y1 += offset.y() - zero_y
                x2 += offset.x() - zero_x
                y2 += offset.y() - zero_y
                if current_pos != (x1, y1):
                    self.gcode_lines.append("M5")
                    self.gcode_lines.append(f"G0 X{x1:.3f} Y{y1:.3f}")
                    current_pos = (x1, y1)
                self.gcode_lines.append("M3")
                self.gcode_lines.append(f"G1 X{x2:.3f} Y{y2:.3f} S{power}")
                current_pos = (x2, y2)

        self.gcode_lines.append("M5")
        self.gcode_lines.append("G0 X0 Y0")
        self.label.setText("G-Code با موفقیت تولید شد")
        self.needs_gcode_update = False

    def update_simulation_paths(self, affected_color=None):
        updated_paths = []
        zero_x, zero_y = self.zero_point.x(), self.zero_point.y()
        for path, item in self.graphics_items:
            if not item.isVisible():
                continue
            item_id = id(item)
            if affected_color and item.normal_pen.color().name() != affected_color:
                if item_id in self.path_cache:
                    updated_paths.append(self.path_cache[item_id])
                continue
            updated_path = []
            for segment_type, p1, p2 in path:
                x1, y1 = p1
                x2, y2 = p2
                p1_scene = item.mapToScene(QPointF(x1, y1))
                p2_scene = item.mapToScene(QPointF(x2, y2))
                new_p1 = (p1_scene.x() - zero_x, p1_scene.y() - zero_y)
                new_p2 = (p2_scene.x() - zero_x, p2_scene.y() - zero_y)
                updated_path.append((segment_type, new_p1, new_p2))
            self.path_cache[item_id] = updated_path
            updated_paths.append(updated_path)

#####################################################################۶۶۶۶۶۶۶۶۶۶۶۶۶     پایان (قسمت ۶) بخش اصلی برنامه
















#########################################                               ۷۷۷۷۷۷۷۷۷            بخش نقطه ورود (قسمت ۷)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CNCApp()
    window.show()
    sys.exit(app.exec_())
