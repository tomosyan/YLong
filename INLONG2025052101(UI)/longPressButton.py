from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, pyqtSignal


class LongPressButton(QPushButton):
    def __init__(self, text="Press Me", parent=None):
        super().__init__(text, parent)
        self.long_press_threshold = 1000  # 长按时间阈值（毫秒）
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_long_press)
        self.is_pressed = False  # 标记按钮是否被按下
        Evevt_jichuliang = pyqtSignal(str)
    def mousePressEvent(self, event):
        """按钮按下时启动计时器"""
        super().mousePressEvent(event)
        self.is_pressed = True
        self.timer.start(self.long_press_threshold)  # 启动计时器

    def mouseReleaseEvent(self, event):
        """按钮释放时停止计时器"""
        super().mouseReleaseEvent(event)
        self.timer.stop()  # 停止计时器
        if self.is_pressed:
            # 如果按下时间不足阈值，视为短按
            print("Short press")
        self.is_pressed = False

    def _on_long_press(self):
        """计时器超时，触发长按事件"""
        #self.timer.stop()
        if self.is_pressed:
            print("Long press detected!")
            # 在这里执行长按操作
            #self.is_pressed = False  # 防止重复触发

if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout()

    btn = LongPressButton("Press and Hold")
    layout.addWidget(btn)

    window.setLayout(layout)
    window.show()
    app.exec_()