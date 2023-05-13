# coding: utf-8
import sys

from PySide2.QtWidgets import (
    QPushButton, QApplication, QHBoxLayout, QVBoxLayout,
    QDialog, QListWidget, QAbstractItemView, QInputDialog)
from link4759.serial_thread.serial_link_4759 import Link4759
from link4759.serial_thread.serial_thread import SerialThread


class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle("link 4759Player")
        # Create widgets
        self.listWidget = QListWidget()
        self.btnPlay = QPushButton("play")
        self.btnStop = QPushButton("stop")
        self.btnCd = QPushButton("change dir")
        self.btnDir = QPushButton("get dir")
        self.btnHelp = QPushButton("help")
        self.btnSend = QPushButton("send")
        # set selectionmode
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.listWidget)
        sublayout = QHBoxLayout()
        sublayout.addWidget(self.btnCd)
        sublayout.addWidget(self.btnDir)
        layout.addLayout(sublayout)
        sublayout = QHBoxLayout()
        sublayout.addWidget(self.btnPlay)
        sublayout.addWidget(self.btnStop)
        layout.addLayout(sublayout)
        sublayout = QHBoxLayout()
        sublayout.addWidget(self.btnHelp)
        sublayout.addWidget(self.btnSend)
        layout.addLayout(sublayout)
        # Set dialog layout
        self.setLayout(layout)
        #
        self.btnCd.clicked.connect(self.click_cd)
        self.btnDir.clicked.connect(self.click_dir)
        self.btnPlay.clicked.connect(self.click_play)
        self.btnStop.clicked.connect(self.click_stop)
        self.btnHelp.clicked.connect(self.click_help)
        self.btnSend.clicked.connect(self.click_send)
        self.listWidget.itemDoubleClicked.connect(self.dblclick_list)
        # connect to 4759Player (& get directory list)
        self.lnk = Link4759()
        self.lnk.connect(baudrate=19200)
        self.lnk.sd_dir()
        self._update_listwidget()
        # create thread
        self.serial_thread = SerialThread(self.lnk.ser, self)
        self.serial_thread.receiving[str].connect(self.receive_str)
        self.serial_thread.start()

    def _update_listwidget(self):
        # update listWidget items
        dispnames = [i.dispname for i in self.lnk.files.items]
        self.listWidget.clear()
        self.listWidget.addItems(dispnames)

    def closeEvent(self, event):
        self.serial_thread.terminate()
        self.lnk.stop()
        del self.lnk

    def receive_str(self, str):
        # print('Signal: receive')
        self.last_receive_str = str
        print(self.last_receive_str, flush=True)

    def dblclick_list(self, item):
        # double click (sd_cd or play)
        res = self.lnk.files.find_item(item.text()) if item and item.text() else None
        if res:
            if res.is_dir:
                self.click_cd()
            else:
                self.click_play()

    def click_help(self):
        # print help
        if not self.serial_thread.isRunning():
            print('thread stopped.')
        else:
            print('thread running.')
            self.lnk.send('help')

    def click_send(self):
        # send command
        if not self.serial_thread.isRunning():
            print('thread stopped.')
        else:
            print('thread running.')
            text, ok = QInputDialog().getText(
                self, "Input command", "command:")
            if ok and text:
                self.lnk.ser.reset_input_buffer()
                self.lnk.send(text)

    def click_dir(self):
        # get directory
        if self.serial_thread.stop():
            self.lnk.sd_dir()
            self._update_listwidget()
            self.serial_thread.start()

    def click_cd(self):
        # change directory (move to child-dir)

        if not self.listWidget.currentItem():
            return

        if self.serial_thread.stop():
            res = self.lnk.files.find_item(self.listWidget.currentItem().text())
            if res:
                self.lnk.sd_cd(res.filename)
                self._update_listwidget()
            self.serial_thread.start()

    def click_play(self):
        # play music

        if self.serial_thread.stop():
            items = self.listWidget.selectedItems()
            if len(items) == 1:
                # single
                res = self.lnk.files.find_item(self.listWidget.currentItem().text())
                if res:
                    self.lnk.play(res.filename, display_name=res.dispname)
            self.serial_thread.start()

    def click_stop(self):
        # stop music

        if self.serial_thread.stop():
            print('')
            self.lnk.stop()
            self.serial_thread.start()


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
