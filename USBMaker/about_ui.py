# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'about_ui.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_About(object):
    def setupUi(self, About):
        About.setObjectName("About")
        About.resize(402, 216)
        self.verticalLayout = QtWidgets.QVBoxLayout(About)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_title = QtWidgets.QLabel(About)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_title.sizePolicy().hasHeightForWidth())
        self.label_title.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(True)
        font.setWeight(75)
        self.label_title.setFont(font)
        self.label_title.setText("USBMaker")
        self.label_title.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.label_title.setObjectName("label_title")
        self.verticalLayout.addWidget(self.label_title)
        self.label_text = QtWidgets.QLabel(About)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.label_text.sizePolicy().hasHeightForWidth())
        self.label_text.setSizePolicy(sizePolicy)
        self.label_text.setTextFormat(QtCore.Qt.RichText)
        self.label_text.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_text.setWordWrap(True)
        self.label_text.setOpenExternalLinks(True)
        self.label_text.setObjectName("label_text")
        self.verticalLayout.addWidget(self.label_text)
        self.label_copyright = QtWidgets.QLabel(About)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_copyright.sizePolicy().hasHeightForWidth())
        self.label_copyright.setSizePolicy(sizePolicy)
        self.label_copyright.setText("Copyright © 2017-2020 Joaquim Monteiro")
        self.label_copyright.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label_copyright.setObjectName("label_copyright")
        self.verticalLayout.addWidget(self.label_copyright)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(30)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_license = QtWidgets.QPushButton(About)
        self.pushButton_license.setObjectName("pushButton_license")
        self.horizontalLayout.addWidget(self.pushButton_license)
        self.pushButton_about_qt = QtWidgets.QPushButton(About)
        self.pushButton_about_qt.setObjectName("pushButton_about_qt")
        self.horizontalLayout.addWidget(self.pushButton_about_qt)
        self.pushButton_close = QtWidgets.QPushButton(About)
        self.pushButton_close.setObjectName("pushButton_close")
        self.horizontalLayout.addWidget(self.pushButton_close)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(About)
        QtCore.QMetaObject.connectSlotsByName(About)

    def retranslateUi(self, About):
        _translate = QtCore.QCoreApplication.translate
        About.setWindowTitle(_translate("About", "About USBMaker"))
        self.label_text.setText(_translate("About", "<html><head/><body><p>USBMaker is a utility to format and make bootable usb drives.</p><p>It\'s written in Python 3 using PyQt5.</p><p>Project page: <a href=\"https://github.com/gmes/USBMaker\"><span style=\" text-decoration: underline; color:#4877b1;\">https://github.com/gmes/USBMaker</span></a></p></body></html>"))
        self.pushButton_license.setText(_translate("About", "License"))
        self.pushButton_about_qt.setText(_translate("About", "About Qt"))
        self.pushButton_close.setText(_translate("About", "Close"))
