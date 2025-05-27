from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from logwindow import Ui_Dialog_log
from PyQt5.QtGui import *


class ui_dialog_log(QDialog, Ui_Dialog_log):
    def __init__(self, name_log, _language, content=None):
        super(ui_dialog_log, self).__init__()
        self.setupUi(self)
        # 头部背景
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 窗体背景透明

        self.setStyleSheet("""
                    QDialog {
                        background: rgba(255,255,255,0.1);
                        border-radius: 8px;
                    }
                """)

        self.label_up.setStyleSheet(
            "border-image:none;color:white;border-image:url(./Image/error.png)")
        self.label_type.setStyleSheet("border-image:none;color:white")
        if _language == "CN":
            self.label_type.setText("请确认")
        else:
            self.label_type.setText("Confirm")
        self.label_content.setStyleSheet("border-image:none;border:none;background-color:transparent;color:white")
        self.label_content.setText(content)
        #self.pushButton.setStyleSheet("QPushButton{border-image:url(./Image/image/keyboard/OK.svg)}"
        #                              "QPushButton:pressed{border-image: url(./Image/image/keyboard/OKON.svg)}")
        #self.pushButton_2.setStyleSheet("QPushButton{border-image:url(./Image/image/keyboard/CANCEL.svg)}"
        #                                    "QPushButton:pressed{border-image: url(./Image/image/keyboard/CANCELON.svg)}")