from keyboard import Ui_Dialog
from PyQt5.QtWidgets import QDialog


class ui_dialog(QDialog, Ui_Dialog):
    def __init__(self):
        super(ui_dialog, self).__init__()
        self.setupUi(self)

        # 头部背景

        self.setStyleSheet("border-image:url(./Image/keyboard/background.svg)")
        self.pushButton_0.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/0.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/0ON.svg)}"
        )
        self.pushButton_1.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/1.svg)}"
            "QPushButton:pressed{border-image: url(./Image/image/keyboard/1ON.svg)}"
        )
        self.pushButton_2.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/2.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/2ON.svg)}"
        )
        self.pushButton_3.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/3.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/3ON.svg)}"
        )
        self.pushButton_4.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/4.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/4ON.svg)}"
        )
        self.pushButton_5.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/5.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/5ON.svg)}"
        )
        self.pushButton_6.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/6.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/6ON.svg)}"
        )
        self.pushButton_7.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/7.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/7ON.svg)}"
        )
        self.pushButton_8.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/8.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/8ON.svg)}"
        )
        self.pushButton_9.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/9.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/9ON.svg)}"
        )
        self.pushButton_m.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/M.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/MON.svg)}"
        )
        self.pushButton_g.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/G.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/GON.svg)}"
        )
        self.pushButton_l.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/L.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/LON.svg)}"
        )
        self.pushButton_x.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/X.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/XON.svg)}"
        )
        self.pushButton_y.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/Y.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/YON.svg)}"
        )
        self.pushButton_z.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/Z.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/ZON.svg)}"
        )
        self.pushButton_e.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/E.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/EON.svg)}"
        )
        self.pushButton_s.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/S.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/SON.svg)}"
        )
        self.pushButton_f.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/F.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/FON.svg)}"
        )
        self.pushButton_t.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/T.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/TON.svg)}"
        )
        self.pushButton_kongge.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/space.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/spaceON.svg)}"
        )
        self.pushButton_dian.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/dot.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/dotON.svg)}"
        )
        self.pushButton_fuhao.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/bar.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/hengON.svg)}"
        )
        self.pushButton_delete.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/delete.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/deleteON.svg)}"
        )
        self.pushButton_cancel.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/cancel.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/cancelON.svg)}"
        )
        self.pushButton_ok.setStyleSheet(
            "QPushButton{border-image:url(./Image/keyboard/OK.svg)}"
            "QPushButton:pressed{border-image: url(./Image/keyboard/OKON.svg)}"
        )

        self.lineEdit.setStyleSheet("border-image:url(./Image/homeImage/ready/lineBackground.svg);color:gray")
        self.label.setStyleSheet("border-image:none;color:gray")
        self.label_2.setStyleSheet("border-image:none;color:gray")
        self.label_3.setStyleSheet("border-image:none;color:gray")

        self.pushButton_0.clicked.connect(self.append_0)
        self.pushButton_1.clicked.connect(self.append_1)
        self.pushButton_2.clicked.connect(self.append_2)
        self.pushButton_3.clicked.connect(self.append_3)
        self.pushButton_4.clicked.connect(self.append_4)
        self.pushButton_5.clicked.connect(self.append_5)
        self.pushButton_6.clicked.connect(self.append_6)
        self.pushButton_7.clicked.connect(self.append_7)
        self.pushButton_8.clicked.connect(self.append_8)
        self.pushButton_9.clicked.connect(self.append_9)
        self.pushButton_m.clicked.connect(self.append_m)
        self.pushButton_g.clicked.connect(self.append_g)
        self.pushButton_l.clicked.connect(self.append_l)
        self.pushButton_x.clicked.connect(self.append_x)
        self.pushButton_y.clicked.connect(self.append_y)
        self.pushButton_z.clicked.connect(self.append_z)
        self.pushButton_e.clicked.connect(self.append_e)
        self.pushButton_s.clicked.connect(self.append_s)
        self.pushButton_f.clicked.connect(self.append_f)
        self.pushButton_t.clicked.connect(self.append_t)
        self.pushButton_kongge.clicked.connect(self.append_kongge)
        self.pushButton_dian.clicked.connect(self.append_dian)
        self.pushButton_fuhao.clicked.connect(self.append_fuhao)
        self.pushButton_delete.clicked.connect(self.append_delete)
        self.pushButton_cancel.clicked.connect(self.cancel)

        self.content_line = ""

    def append_0(self):
        self.content_line += "0"
        self.lineEdit.setText(self.content_line)

    def append_1(self):
        self.content_line += "1"
        self.lineEdit.setText(self.content_line)

    def append_2(self):
        self.content_line += "2"
        self.lineEdit.setText(self.content_line)

    def append_3(self):
        self.content_line += "3"
        self.lineEdit.setText(self.content_line)

    def append_4(self):
        self.content_line += "4"
        self.lineEdit.setText(self.content_line)

    def append_5(self):
        self.content_line += "5"
        self.lineEdit.setText(self.content_line)

    def append_6(self):
        self.content_line += "6"
        self.lineEdit.setText(self.content_line)

    def append_7(self):
        self.content_line += "7"
        self.lineEdit.setText(self.content_line)

    def append_8(self):
        self.content_line += "8"
        self.lineEdit.setText(self.content_line)

    def append_9(self):
        self.content_line += "9"
        self.lineEdit.setText(self.content_line)

    def append_m(self):
        self.content_line += "M"
        self.lineEdit.setText(self.content_line)

    def append_g(self):
        self.content_line += "G"
        self.lineEdit.setText(self.content_line)

    def append_l(self):
        self.content_line += "L"
        self.lineEdit.setText(self.content_line)

    def append_x(self):
        self.content_line += "X"
        self.lineEdit.setText(self.content_line)

    def append_y(self):
        self.content_line += "Y"
        self.lineEdit.setText(self.content_line)

    def append_z(self):
        self.content_line += "Z"
        self.lineEdit.setText(self.content_line)

    def append_e(self):
        self.content_line += "E"
        self.lineEdit.setText(self.content_line)

    def append_s(self):
        self.content_line += "S"
        self.lineEdit.setText(self.content_line)

    def append_f(self):
        self.content_line += "F"
        self.lineEdit.setText(self.content_line)

    def append_t(self):
        self.content_line += "T"
        self.lineEdit.setText(self.content_line)

    def append_kongge(self):
        self.content_line += " "
        self.lineEdit.setText(self.content_line)

    def append_dian(self):
        self.content_line += "."
        self.lineEdit.setText(self.content_line)

    def append_fuhao(self):
        self.content_line += "-"
        self.lineEdit.setText(self.content_line)

    def append_delete(self):
        self.content_line = self.content_line[0:len(self.content_line) - 1]
        self.lineEdit.setText(self.content_line)

    def cancel(self):
        self.content_line = ""
        self.lineEdit.setText("")
        self.hide()
