from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from openfile import Ui_Dialog_file

class ui_dialog_file(QDialog,Ui_Dialog_file):
    def __init__(self):
        super(ui_dialog_file, self).__init__()
        self.setupUi(self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        self.setStyleSheet("""
            QDialog {
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
            }
        """)

        # 美化取消按钮
        self.pushButton.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.3);
                border-radius: 15px;
                border: 1px solid rgba(255,255,255,0.2);
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.2);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.1);
            }
        """)

        # 美化确定按钮
        self.pushButton_2.setStyleSheet("""
            QPushButton {
                background: rgba(242,95,13,0.8);
                border-radius: 15px;
                border: 1px solid rgba(255,255,255,0.2);
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background: rgba(242,95,13,0.9);
            }
            QPushButton:pressed {
                background: rgba(242,95,13,0.7);
            }
        """)
        self.pushButton.clicked.connect(self.cencel)
        self.listView_file.setStyleSheet('border-image:none;border:none;background-color:transparent;color:gray')
        self.open_gcodefile = ""

    def cencel(self):
        self.hide()