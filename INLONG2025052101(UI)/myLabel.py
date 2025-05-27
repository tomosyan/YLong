from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
class myImgLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super(myImgLabel, self).__init__(parent)
        f = QFont("ZYSong18030", 10)  # 设置字体,字号
        self.setFont(f)  # 未来自定义事件后，该两句删掉或注释掉
        self.flag = 1

    '''重载一下鼠标按下事件(单击)'''
    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:  # 左键按下
            if self.flag == 1:
                print(1)
                self.myLabelMax()
                self.flag = 0
            else:
                print(0)
                self.myLabelMin()
                self.flag = 1

    def mouseDoubieCiickEvent(self, event):
        #        if event.buttons () == QtCore.Qt.LeftButton:                           # 左键按下
        #            self.setText ("双击鼠标左键的功能: 自己定义")
        pass

    '''重载一下鼠标键释放事件'''

    def mouseReleaseEvent(self, event):
        pass
        #self.setText("鼠标释放事件: 自己定义")

    '''重载一下鼠标移动事件'''

    def mouseMoveEvent(self, event):
        self.setText("鼠标移动事件: 自己定义")

    def myLabelMax(self):
        desktop_screen = QtWidgets.QApplication.desktop().screenGeometry()
        self.setWindowFlags(Qt.Dialog)
        #self.setFixedSize(desktop_screen.width(), desktop_screen.height())
        self.showFullScreen()

    def myLabelMin(self):
        desktop_screen = QtWidgets.QApplication.desktop().screenGeometry()
        self.setWindowFlags(Qt.SubWindow| Qt.WindowStaysOnBottomHint)
        #self.setFixedSize(desktop_screen.width(), desktop_screen.height())
        self.showNormal()
        self.resize(781, 351)
        self.move(12, 12)
        self.lower()