from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        self.textBrowser = QtWidgets.QTextBrowser(Form)
        self.textBrowser.setGeometry(QtCore.QRect(20, 10, 351, 291))
        self.textBrowser.setObjectName("textBrowser")
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(400, 20, 54, 12))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setGeometry(QtCore.QRect(400, 60, 54, 12))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setGeometry(QtCore.QRect(400, 110, 54, 12))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(Form)
        self.label_4.setGeometry(QtCore.QRect(400, 170, 54, 12))
        self.label_4.setObjectName("label_4")
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(390, 220, 75, 23))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(Form)
        self.pushButton.clicked.connect(self.showname)
        QtCore.QMetaObject.connectSlotsByName(Form)
    def showname(self):
        self.label.setText("leibso")
    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "TextLabel"))
        self.label_2.setText(_translate("Form", "TextLabel"))
        self.label_3.setText(_translate("Form", "TextLabel"))
        self.label_4.setText(_translate("Form", "leibso"))
        self.pushButton.setText(_translate("Form", "PushButton"))

if __name__=='__main__':

    app = QtWidgets.QApplication(sys.argv)
    widget = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(widget)
    widget.show()
    sys.exit(app.exec_())
