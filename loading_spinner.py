import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen

class LoadingSpinner(QWidget):
    def __init__(self, parent=None, size=64, num_dots=8, color=Qt.GlobalColor.blue):
        super().__init__(parent)
        self.size = size
        self.num_dots = num_dots
        self.color = color
        self.current_dot = 0
        
        # 设置定时器用于动画
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.setInterval(100)  # 100ms per frame
        
        # 设置窗口属性
        self.setFixedSize(size, size)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def start(self):
        self.show()
        self.timer.start()
    
    def stop(self):
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        self.current_dot = (self.current_dot + 1) % self.num_dots
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = self.size / 2
        dot_radius = self.size / 20
        radius = (self.size - dot_radius * 2) / 2
        
        for i in range(self.num_dots):
            angle = 2 * 3.14159 * i / self.num_dots
            x = center + radius * math.cos(angle)
            y = center + radius * math.sin(angle)
            
            opacity = (i - self.current_dot) % self.num_dots / self.num_dots
            color = QColor(self.color)
            color.setAlphaF(opacity)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(int(x - dot_radius), int(y - dot_radius), 
                              int(dot_radius * 2), int(dot_radius * 2))