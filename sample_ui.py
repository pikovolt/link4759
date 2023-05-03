# coding: utf-8
import sys
from PySide2.QtWidgets import (
    QLineEdit, QPushButton, QApplication, QVBoxLayout, QDialog, QListWidget)
from serial_link_4759 import Link4759

class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        # Create widgets
        self.listWidget = QListWidget()
        self.btnPlay = QPushButton("play")
        self.btnStop = QPushButton("stop")
        self.btnParent = QPushButton("parent dir")
        self.btnCd = QPushButton("change dir")
        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.listWidget)
        layout.addWidget(self.btnCd)
        layout.addWidget(self.btnParent)
        layout.addWidget(self.btnPlay)
        layout.addWidget(self.btnStop)
        # Set dialog layout
        self.setLayout(layout)
        self.btnCd.clicked.connect(self.click_cd)
        self.btnParent.clicked.connect(self.click_parent)
        self.btnPlay.clicked.connect(self.click_play)
        self.btnStop.clicked.connect(self.click_stop)
        # connect to 4759Player (& get directory list)
        self.lnk = Link4759()
        self.lnk.connect()
        self.lnk.sd_dir()
        # update ListWidget
        self.listWidget.addItems(self.lnk.files)

    def click_cd(self):
        # change directory (move to child-dir)
        self.lnk.sd_cd(self.listWidget.currentItem().text())
        self.listWidget.clear()
        self.listWidget.addItems(self.lnk.files)

    def click_parent(self):
        # change directory (move to parent-dir)
        self.lnk.sd_cd('..')
        self.listWidget.clear()
        self.listWidget.addItems(self.lnk.files)

    def click_play(self):
        # play music
        self.lnk.play(self.listWidget.currentItem().text())

    def click_stop(self):
        # stop music
        self.lnk.stop()

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
