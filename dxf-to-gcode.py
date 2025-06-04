import ezdxf
import argparse
import math
import os

class DXFtoGCode:
    def __init__(self, feed_rate=200, safe_height=5.0, cut_depth=-1.0):
        """
        پارامترهای اولیه برای تبدیل DXF به G-code
        
        Args:
            feed_rate (float): سرعت حرکت (mm/min)
            safe_height (float): ارتفاع امن برای حرکت بدون برش (mm)
            cut_depth (float): عمق برش (mm) - مقدار منفی
        """
        self.feed_rate = feed_rate
        self.safe_height = safe_height
        self.cut_depth = cut_depth
        self.gcode = []
        
    def header(self):
        """تولید سربرگ G-code"""
        self.gcode.append("G21 ; set units to millimeters")
        self.gcode.append("G90 ; use absolute coordinates")
        self.gcode.append("G17 ; XY plane selection")
        self.gcode.append(f"G0 Z{self.safe_height} ; move to safe height")
        self.gcode.append("G0 X0 Y0 ; move to origin")
        
    def footer(self):
        """تولید پایان G-code"""
        self.gcode.append(f"G0 Z{self.safe_height} ; move to safe height")
        self.gcode.append("G0 X0 Y0 ; return to origin")
        self.gcode.append("M2 ; end program")
        
    def move_to_point(self, x, y, z=None, feed=None):
        """
        ایجاد دستور حرکت به نقطه مشخص
        
        Args:
            x, y: مختصات نقطه هدف
            z: ارتفاع (اختیاری)
            feed: سرعت حرکت (اختیاری)
        """
        cmd = "G0" if feed is None else "G1"
        position = f"X{x:.4f} Y{y:.4f}"
        
        if z is not None:
            position += f" Z{z:.4f}"
            
        if feed is not None:
            position += f" F{feed}"
            
        self.gcode.append(f"{cmd} {position}")
        
    def process_line(self, line):
        """پردازش یک خط"""
        start = (line.dxf.start.x, line.dxf.start.y)
        end = (line.dxf.end.x, line.dxf.end.y)
        
        # حرکت به نقطه شروع
        self.move_to_point(start[0], start[1])
        # پایین آوردن ابزار برای برش
        self.move_to_point(start[0], start[1], self.cut_depth, self.feed_rate)
        # حرکت به نقطه پایان
        self.move_to_point(end[0], end[1], feed=self.feed_rate)
        # بالا بردن ابزار
        self.move_to_point(end[0], end[1], self.safe_height)
        
    def process_circle(self, circle):
        """پردازش یک دایره"""
        center = (circle.dxf.center.x, circle.dxf.center.y)
        radius = circle.dxf.radius
        
        # حرکت به نقطه شروع دایره (سمت راست مرکز)
        start_x = center[0] + radius
        start_y = center[1]
        
        # حرکت به نقطه شروع
        self.move_to_point(start_x, start_y)
        # پایین آوردن ابزار برای برش
        self.move_to_point(start_x, start_y, self.cut_depth, self.feed_rate)
        
        # افزودن دستور G-code برای حرکت دایره‌ای (G02: ساعتگرد، G03: پادساعتگرد)
        self.gcode.append(f"G03 X{start_x:.4f} Y{start_y:.4f} I{-radius:.4f} J0 F{self.feed_rate}")
        
        # بالا بردن ابزار
        self.move_to_point(start_x, start_y, self.safe_height)
    
    def process_arc(self, arc):
        """پردازش یک کمان"""
        center = (arc.dxf.center.x, arc.dxf.center.y)
        radius = arc.dxf.radius
        start_angle = math.radians(arc.dxf.start_angle)
        end_angle = math.radians(arc.dxf.end_angle)
        
        # محاسبه نقاط شروع و پایان
        start_x = center[0] + radius * math.cos(start_angle)
        start_y = center[1] + radius * math.sin(start_angle)
        end_x = center[0] + radius * math.cos(end_angle)
        end_y = center[1] + radius * math.sin(end_angle)
        
        # محاسبه آفست مرکز نسبت به نقطه شروع
        i = center[0] - start_x
        j = center[1] - start_y
        
        # حرکت به نقطه شروع
        self.move_to_point(start_x, start_y)
        # پایین آوردن ابزار برای برش
        self.move_to_point(start_x, start_y, self.cut_depth, self.feed_rate)
        
        # تعیین جهت کمان (ساعتگرد یا پادساعتگرد)
        cmd = "G02" if (end_angle - start_angle) % (2*math.pi) < math.pi else "G03"
        self.gcode.append(f"{cmd} X{end_x:.4f} Y{end_y:.4f} I{i:.4f} J{j:.4f} F{self.feed_rate}")
        
        # بالا بردن ابزار
        self.move_to_point(end_x, end_y, self.safe_height)
        
    def process_polyline(self, polyline):
        """پردازش یک چندخطی"""
        points = []
        
        # جمع‌آوری تمام نقاط چندخطی
        for vertex in polyline.vertices:
            points.append((vertex.dxf.location.x, vertex.dxf.location.y))
            
        if not points:
            return
            
        # حرکت به اولین نقطه
        self.move_to_point(points[0][0], points[0][1])
        # پایین آوردن ابزار برای برش
        self.move_to_point(points[0][0], points[0][1], self.cut_depth, self.feed_rate)
        
        # حرکت به تمام نقاط بعدی
        for x, y in points[1:]:
            self.move_to_point(x, y, feed=self.feed_rate)
            
        # بستن چندخطی اگر بسته باشد
        if polyline.is_closed:
            self.move_to_point(points[0][0], points[0][1], feed=self.feed_rate)
            
        # بالا بردن ابزار
        self.move_to_point(points[-1][0], points[-1][1], self.safe_height)
        
    def process_lwpolyline(self, lwpolyline):
        """پردازش یک چندخطی سبک"""
        points = []
        
        # جمع‌آوری تمام نقاط چندخطی سبک
        for point in lwpolyline:
            points.append((point[0], point[1]))
            
        if not points:
            return
            
        # حرکت به اولین نقطه
        self.move_to_point(points[0][0], points[0][1])
        # پایین آوردن ابزار برای برش
        self.move_to_point(points[0][0], points[0][1], self.cut_depth, self.feed_rate)
        
        # حرکت به تمام نقاط بعدی
        for x, y in points[1:]:
            self.move_to_point(x, y, feed=self.feed_rate)
            
        # بستن چندخطی اگر بسته باشد
        if lwpolyline.closed:
            self.move_to_point(points[0][0], points[0][1], feed=self.feed_rate)
            
        # بالا بردن ابزار
        last_point = points[-1]
        self.move_to_point(last_point[0], last_point[1], self.safe_height)
        
    def process_spline(self, spline):
        """پردازش یک اسپلاین با تقریب به چندخطی"""
        # تقریب اسپلاین به چندخطی با 50 قطعه
        points = spline.approximate(segments=50)
        
        if not points:
            return
            
        # حرکت به اولین نقطه
        self.move_to_point(points[0][0], points[0][1])
        # پایین آوردن ابزار برای برش
        self.move_to_point(points[0][0], points[0][1], self.cut_depth, self.feed_rate)
        
        # حرکت به تمام نقاط بعدی
        for x, y, _ in points[1:]:
            self.move_to_point(x, y, feed=self.feed_rate)
            
        # بالا بردن ابزار
        last_point = points[-1]
        self.move_to_point(last_point[0], last_point[1], self.safe_height)
    
    def process_dxf(self, dxf_file):
        """
        پردازش فایل DXF و تبدیل به G-code
        
        Args:
            dxf_file: مسیر فایل DXF
        
        Returns:
            list: لیست خطوط G-code
        """
        try:
            doc = ezdxf.readfile(dxf_file)
            msp = doc.modelspace()
            
            # افزودن سربرگ
            self.header()
            
            # پردازش انواع نهادهای DXF
            for entity in msp:
                if entity.dxftype() == 'LINE':
                    self.process_line(entity)
                elif entity.dxftype() == 'CIRCLE':
                    self.process_circle(entity)
                elif entity.dxftype() == 'ARC':
                    self.process_arc(entity)
                elif entity.dxftype() == 'POLYLINE':
                    self.process_polyline(entity)
                elif entity.dxftype() == 'LWPOLYLINE':
                    self.process_lwpolyline(entity)
                elif entity.dxftype() == 'SPLINE':
                    self.process_spline(entity)
                    
            # افزودن پایان
            self.footer()
            
            return self.gcode
            
        except ezdxf.DXFError as e:
            print(f"خطا در خواندن فایل DXF: {str(e)}")
            return []
        except Exception as e:
            print(f"خطا: {str(e)}")
            return []
            
def main():
    """تابع اصلی برنامه"""
    parser = argparse.ArgumentParser(description='تبدیل فایل DXF به G-code برای CNC دو محوره')
    parser.add_argument('input', help='مسیر فایل ورودی DXF')
    parser.add_argument('--output', '-o', help='مسیر فایل خروجی G-code')
    parser.add_argument('--feed-rate', '-f', type=float, default=200, help='سرعت حرکت (mm/min)')
    parser.add_argument('--safe-height', '-s', type=float, default=5.0, help='ارتفاع امن برای حرکت (mm)')
    parser.add_argument('--cut-depth', '-d', type=float, default=-1.0, help='عمق برش (mm)')
    
    args = parser.parse_args()
    
    # مقدار پیش‌فرض برای فایل خروجی اگر مشخص نشده باشد
    if args.output is None:
        base_name = os.path.splitext(os.path.basename(args.input))[0]
        args.output = f"{base_name}.gcode"
    
    # ایجاد نمونه از کلاس تبدیل
    converter = DXFtoGCode(
        feed_rate=args.feed_rate,
        safe_height=args.safe_height,
        cut_depth=args.cut_depth
    )
    
    # تبدیل DXF به G-code
    gcode = converter.process_dxf(args.input)
    
    # ذخیره G-code در فایل
    if gcode:
        with open(args.output, 'w') as f:
            f.write('\n'.join(gcode))
        print(f"فایل G-code با موفقیت در {args.output} ذخیره شد.")
    else:
        print("خطا در تبدیل فایل DXF.")

if __name__ == "__main__":
    main()
