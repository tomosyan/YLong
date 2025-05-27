# from PyQt5.QtWidgets import QApplication, QMainWindow, QGroupBox, QVBoxLayout, QWidget
#
#
# class TestWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("QGroupBox 圆角调试")
#         self.resize(30, 60)
#
#         # 创建 QGroupBox
#         self.groupBox_8 = QGroupBox("测试圆角", self)
#         self.groupBox_8.setStyleSheet("""
#             QGroupBox {
#                 background-color: rgba(132,151,176,0.1);
#                 border: 1px solid rgba(255, 255, 255, 0.2);
#                 border-top-left-radius: 40px;
#                 border-top-right-radius: 40px;
#                 padding-top: 15px;
#             }
#             QGroupBox::title {
#                 subcontrol-origin: padding;
#                 left: 10px;
#             }
#         """)
#
#         # 设置布局
#         layout = QVBoxLayout()
#         layout.addWidget(self.groupBox_8)
#
#         container = QWidget()
#         container.setLayout(layout)
#         self.setCentralWidget(container)
#
#
# if __name__ == "__main__":
#     app = QApplication([])
#     window = TestWindow()
#     window.show()
#     app.exec_()
import sys

from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene

# from PyQt5.QtWidgets import QApplication, QMainWindow
# from PyQt5.QtGui import QPixmap
# from untitled import  Ui_MainWindow
# class ImageViewer(QMainWindow,Ui_MainWindow):
#     def __init__(self):
#         super(ImageViewer,self).__init__()
#         self.setupUi(self)
#
#
#         # 创建一个QGraphicsScene
#         scene = QGraphicsScene(self)
#         # 创建一个QPixmap并加载图片
#         pixmap = QPixmap('D:\INLONG2025050801\Image\logo.png')
#
#         # 在场景中添加一个图像项
#         scene.addPixmap(pixmap)
#
#         # 将场景设置为视图的场景
#         self.graphicsView.setScene(scene)
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = ImageViewer()
#     window.show()
#     sys.exit(app.exec_())
#
# import sys
# from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout,QHBoxLayout, QWidget, QApplication
#
#
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.initUI()
#
#     def initUI(self):
#         self.central_widget = QWidget()
#         self.setCentralWidget(self.central_widget)
#
#         self.left_layout = QHBoxLayout()
#         self.central_widget.setLayout(self.left_layout)
#
#         self.button1 = QPushButton('Show Widget 1')
#         self.button2 = QPushButton('Show Widget 2')
#
#         self.widget1 = QWidget()
#         self.widget2 = QWidget()
#
#         self.left_layout.addWidget(self.button1)
#         self.left_layout.addWidget(self.button2)
#
#         self.button1.clicked.connect(lambda: self.switch_widget(self.widget1))
#         self.button2.clicked.connect(lambda: self.switch_widget(self.widget2))
#
#         self.switch_widget(self.widget1)
#
#     def switch_widget(self, widget):
#         if hasattr(self, 'current_widget'):
#             self.left_layout.removeWidget(self.current_widget)
#             self.current_widget.setParent(None)
#         self.left_layout.addWidget(widget)
#         self.current_widget = widget
#
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     mainWin = MainWindow()
#     mainWin.show()
#     sys.exit(app.exec_())
import sys
from PyQt5.QtWidgets import QWidget, QToolTip, QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys


class ChildOneWin(QWidget):
    def __init__(self, parent=None):
        super(ChildOneWin, self).__init__(parent)

        self.main_layout = QVBoxLayout()
        self.top_widget = QWidget()
        self.setLayout(self.main_layout)
        self.top_widget.setObjectName("ChildOneWin_wdt")
        self.top_widget.setStyleSheet("#ChildOneWin_wdt{background:rgb(255,255,255)}")
        self.main_layout.addWidget(self.top_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        top_widget_layout = QVBoxLayout()
        self.top_widget.setLayout(top_widget_layout)

        self.test_btn = QPushButton('窗口1')
        top_widget_layout.addStretch(1)
        top_widget_layout.addWidget(self.test_btn)


class ChildTwoWin(QWidget):
    def __init__(self, parent=None):
        super(ChildTwoWin, self).__init__(parent)

        self.main_layout = QVBoxLayout()

        self.top_widget = QWidget()
        self.setLayout(self.main_layout)
        self.top_widget.setObjectName("ChildTwoWin_wdt")
        self.top_widget.setStyleSheet("#ChildTwoWin_wdt{background:rgb(255,0,0)}")
        self.main_layout.addWidget(self.top_widget)

        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        top_widget_layout = QVBoxLayout()
        self.top_widget.setLayout(top_widget_layout)

        self.test_btn = QPushButton('窗口2')
        top_widget_layout.addStretch(1)
        top_widget_layout.addWidget(self.test_btn)
        top_widget_layout.addStretch(1)


class ChildThreeWin(QWidget):
    def __init__(self, parent=None):
        super(ChildThreeWin, self).__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.BypassWindowManagerHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.wdt = QWidget()
        #self.wdt.setAttribute(Qt.WA_TranslucentBackground)
        self.wdt.setObjectName("tipWaitingWindow_back")
        self.wdt.setStyleSheet("#tipWaitingWindow_back{background:rgba(0,0,0,0.2)}")

        self.layout = QGridLayout(self)
        self.layout.addWidget(self.wdt)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        main_layout = QVBoxLayout()

        self.wdt.setLayout(main_layout)

        self.test_btn = QPushButton('窗口3')
        main_layout.addWidget(self.test_btn)
        main_layout.addStretch(1)


class WinUIform(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('透明窗口测试')
        self.resize(500, 500)

        main_layout = QVBoxLayout()

        self.setLayout(main_layout)


        top_widget = QWidget()
        top_widget_layout = QHBoxLayout()
        top_widget.setLayout(top_widget_layout)

        self.test_btn = QPushButton('测试')
        self.test_btn.clicked.connect(self.call_back_test_btn)

        self.control_btn = QPushButton('控制')
        self.control_btn.clicked.connect(self.call_back_control_btn)

        self.show_btn = QPushButton('显示')
        self.show_btn.clicked.connect(self.call_back_show_btn)

        top_widget_layout.addWidget(self.test_btn)
        top_widget_layout.addStretch(1)
        top_widget_layout.addWidget(self.control_btn)
        top_widget_layout.addStretch(1)
        top_widget_layout.addWidget(self.show_btn)

        self.bottom_widget = QWidget()

        main_layout.addWidget(top_widget)
        main_layout.addWidget(self.bottom_widget)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 5)

        self.child_one_win = ChildOneWin()
        self.child_two_win = ChildTwoWin()
        self.child_three_win = ChildThreeWin()

        self.bottom_widget_layout = QHBoxLayout()

        self.bottom_widget.setLayout(self.bottom_widget_layout)
        self.bottom_widget_layout.addWidget(self.child_one_win)
        #self.bottom_widget_layout.addChildWidget(self.child_two_win)

        #self.child_two_win.setGeometry(50, 50, 200, 200)

    def call_back_show_btn(self):
        top_rect = self.bottom_widget.geometry()
        print(top_rect)
        self.bottom_widget_layout.addChildWidget(self.child_three_win)
        self.child_three_win.resize(top_rect.width(), top_rect.height())

    def call_back_test_btn(self):
        pass

    def call_back_control_btn(self):
        pass




if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 下面两种方法都可以
    win = WinUIform()
    #win = Winform()
    win.show()
    sys.exit(app.exec_())
