from PyQt5 import QtCore, QtGui, QtWidgets
import time
from testgood import Ui_Form
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):

        self.child = ChildrenForm()
        self.child1 = ChildrenForm()
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 800)
        MainWindow.setAutoFillBackground(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lcdNumber_2 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdNumber_2.setGeometry(QtCore.QRect(650, 10, 41, 23))
        self.lcdNumber_2.setObjectName("lcdNumber_2")
        self.lcdNumber_3 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdNumber_3.setGeometry(QtCore.QRect(700, 10, 41, 23))
        self.lcdNumber_3.setObjectName("lcdNumber_3")
        self.lcdNumber_4 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdNumber_4.setGeometry(QtCore.QRect(750, 10, 41, 23))
        self.lcdNumber_4.setObjectName("lcdNumber_4")
        self.lcdNumber = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdNumber.setGeometry(QtCore.QRect(600, 10, 41, 23))
        self.lcdNumber.setObjectName("lcdNumber")
        self.labelIP = QtWidgets.QLabel(self.centralwidget)
        self.labelIP.setGeometry(QtCore.QRect(50, 300, 31, 20))
        self.labelIP.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.labelIP.setObjectName("labelIP")
        self.gridLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(30, 20, 600, 600))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.MaingridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.MaingridLayout.setContentsMargins(0, 0, 0, 0)
        self.MaingridLayout.setObjectName("MaingridLayout")
        self.ButtonShow = QtWidgets.QPushButton(self.centralwidget)
        self.ButtonShow.setGeometry(QtCore.QRect(620, 100, 75, 23))
        self.ButtonShow.setObjectName("ButtonShow")

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        self.menubar.setObjectName("menubar")
        self.menufile = QtWidgets.QMenu(self.menubar)
        self.menufile.setObjectName("menufile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menufile.menuAction())

        self.retranslateUi(MainWindow)
        self.ButtonShow.clicked.connect(self.showthewindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
    def showthewindow(self):
        self.MaingridLayout.addChildWidget(self.child1)
        self.child1.resize(self.centralwidget.width()+100, self.centralwidget.height()+100)
        self.child1.show()
        # self.MaingridLayout.addChildWidget(self.child)
        # self.child.show()
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.labelIP.setText(_translate("MainWindow", "IP"))
        self.ButtonShow.setText(_translate("MainWindow", "展示"))
        self.menufile.setTitle(_translate("MainWindow", "file"))

class ChildrenForm(QtWidgets.QWidget,Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainwindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(mainwindow)
    mainwindow.show()
    sys.exit(app.exec_())
