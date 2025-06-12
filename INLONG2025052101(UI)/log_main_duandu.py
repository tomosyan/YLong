from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from logwindow_duandu import Ui_Dialog_log
from PyQt5.QtGui import *


class ui_dialog_log_duandu(QDialog, Ui_Dialog_log):
    def __init__(self, name_log, _language, content=None):
        super(ui_dialog_log_duandu, self).__init__()
        self.setupUi(self)
        # 头部背景
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        if _language == "CN":
            #self.open_un.setText("门开关")
            pass
        else:
            #self.open_un.setText("Door\nswitch")
            self.pushButton_heatup.setText("Heat")
            self.pushButton_Return.setText("Return")
            self.pushButton_Load.setText("Feed")
            self.pushButton_down.setText("Drop")
        if name_log == "yindao":
            self.label_up.setStyleSheet(
                "border-image:none;color:white;border-image:url(./Image/warningImage/yindao.svg)")
            self.label_type.setStyleSheet("border-image:none;color:white")
            if _language == "CN":
                self.label_type.setText("请确认")
            else:
                self.label_type.setText("Confirm")
            self.label_content.setStyleSheet("border-image:none;border:none;background-color:transparent;color:white")
            self.label_content.setText(content)
            self.pushButton_ok.setStyleSheet("QPushButton{border-image:url(./Image/image/keyboard/OK.svg)}"
                                          "QPushButton:pressed{border-image: url(./Image/image/keyboard/OKON.svg)}")
            self.pushButton_no.setStyleSheet("QPushButton{border-image:url(./Image/image/keyboard/CANCEL.svg)}"
                                            "QPushButton:pressed{border-image: url(./Image/image/keyboard/CANCELON.svg)}")
        if name_log == "zhuyi":
            self.label_up.setStyleSheet(
                "border-image:none;color:white;border-image:url(./Image/warningImage/zhuyi.svg)")
            self.label_type.setStyleSheet("border-image:none;color:white")
            if _language == "CN":
                self.label_type.setText("注意")
            else:
                self.label_type.setText("Attention")

            self.label_content.setStyleSheet("border-image:none;border:none;background-color:transparent;color:white")
            self.label_content.setText(content)
            self.pushButton_ok.setStyleSheet("QPushButton{border-image:url(./Image/image/keyboard/OK.svg)}"
                                          "QPushButton:pressed{border-image: url(./Image/image/keyboard/OKON.svg)}")
            self.pushButton_no.setStyleSheet("QPushButton{border-image:url(./Image/image/keyboard/CANCEL.svg)}"
                                            "QPushButton:pressed{border-image: url(./Image/image/keyboard/CANCELON.svg)}")
        if name_log == "cuowu":
            self.label_up.setStyleSheet(
                "border-image:none;color:white;border-image:url(./Image/warningImage/cuowu.svg)")
            self.label_type.setStyleSheet("border-image:none;color:white")
            if _language == "CN":
                self.label_type.setText("错误")
            else:
                self.label_type.setText("Error")

            self.label_content.setStyleSheet(
            "border-image:none;border:none;background-color:transparent;color:white")
            self.label_content.setText(content)
            self.label_content.setWordWrap(1)
            self.pushButton_ok.setStyleSheet("QPushButton{border-image:url(./Image/image/keyboard/OK.svg)}"
                                      "QPushButton:pressed{border-image: url(./Image/image/keyboard/OKON.svg)}")
            self.pushButton_no.setStyleSheet("QPushButton{border-image:url(./Image/image/keyboard/CANCEL.svg)}"
                                        "QPushButton:pressed{border-image: url(./Image/image/keyboard/CANCELON.svg)}")



import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = ui_dialog_log_duandu("zhuyi", "CN", "请检查是否发生堵料")
    main.show()
    app.exec_()
    del app