#继承QPushButton重写paintEvent
import sys

from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap, QBrush
from PyQt5.QtWidgets import QPushButton, QApplication, QWidget, QVBoxLayout, QStyle, QStyleOption, QMainWindow, \
    QHBoxLayout
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap
class CustomButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super(CustomButton, self).__init__(*args, **kwargs)
        self.setMinimumHeight(100)
        self.setStyleSheet("background-color: red; color: red;")
    # def paintEvent(self, event):
    #     pass

        #painter = QPainter(self)
        # painter.setRenderHint(QPainter.Antialiasing, True)
        # pen = QPen()
        # pen.setWidth(1)
        # pen.setColor(QColor(200, 200, 200))
        # painter.setPen(pen)
        #pixmap=QPixmap("D:/INLONG20250501401/INLONG20250501401/Image/up.png")
        #painter.drawPixmap(0,0,pixmap.height())
        #painter.translate(50, 50)
        #painter.drawPixmap(0, 0, 50, 50, pixmap)
        # pixmap = pixmap.scaled(pixmap.width()*2, pixmap.height()*2, Qt.KeepAspectRatio)
        # painter.drawPixmap(50, 50, pixmap)
        # if not self.is_state:
        #     painter.setBrush(Qt.gray)
        #     painter.drawEllipse(0, 0, self.width(), self.height())
        #     painter.setBrush(Qt.white)
        #     painter.drawEllipse(0, 0, 40, 40)
        # else:
        #     painter.setBrush(Qt.green)
        #     painter.drawEllipse(0, 0, self.width(), self.height())
        #     painter.setBrush(Qt.white)
        #     painter.drawEllipse(self.width() - 40, self.height() - 40, 40, 40)
        # opt = QStyleOption()
        # opt.initFrom(self)
        # self.style().drawPrimitive(QStyle.PE_Widget, opt, self.painter, self)
        # self.style().drawPrimitive(QStyle.PE_Widget, opt, self.painter, self)
    # def mousePressEvent(self, event):
    #     self.is_state = not self.is_state
    #     self.update()
    #     super().mousePressEvent(event)
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Custom QPushButton Example")
        self.setGeometry(100, 100, 300, 200)

        # 创建自定义按钮
        self.button1 = CustomButton(self)
        self.button2 = CustomButton(self)
        self.button3 = CustomButton(self)

        # 设置布局
        layout = QHBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())