# coding: utf-8
import os
import sys

module_path = os.path.expandvars(os.environ['PY_MODULE_PATH'])
sys.path.append(module_path)

from PySide2.QtWidgets import (
    QPushButton, QApplication, QHBoxLayout, QVBoxLayout,
    QDialog, QListWidget, QAbstractItemView, QInputDialog)
from serial_link_4759 import Link4759
from ui_thread import PlayListThread


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
        self.btnNext = QPushButton("list next")
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
        layout.addWidget(self.btnNext)
        # Set dialog layout
        self.setLayout(layout)
        self.btnCd.clicked.connect(self.click_cd)
        self.btnDir.clicked.connect(self.click_dir)
        self.btnPlay.clicked.connect(self.click_play)
        self.btnStop.clicked.connect(self.click_stop)
        self.btnHelp.clicked.connect(self.click_help)
        self.btnSend.clicked.connect(self.click_send)
        self.btnNext.clicked.connect(self.click_next)
        self.listWidget.itemDoubleClicked.connect(self.dblclick_list)
        # connect to 4759Player (& get directory list)
        self.lnk = Link4759()
        self.lnk.connect(baudrate=19200)
        self.lnk.sd_dir()
        self._update_listwidget()
        # create thread
        self.multi = PlayListThread([], self.lnk, parent=self)

    def _update_listwidget(self):
        # update listWidget items
        dispnames = [i.dispname for i in self.lnk.files.items]
        self.listWidget.clear()
        self.listWidget.addItems(dispnames)

    def closeEvent(self, event):
        if self.multi:
            self.multi.stop()
            self.multi.quit()
            self.multi.wait()
        self.lnk.stop()
        del self.lnk

    def dblclick_list(self, item):
        # double click (sd_cd or play)
        res = self.lnk.files.find_item(item.text()) if item and item.text() else None
        if res:
            if res.is_dir:
                self.click_cd()
            else:
                self.click_play()

    def click_next(self):
        # list next
        self.multi.cmd('next')

    def click_help(self):
        # print help
        self.multi.mutex_send('help')

    def click_send(self):
        # send command
        text, ok = QInputDialog().getText(
            self, "Input command", "command:")
        if ok and text:
            self.multi.mutex_send(text)

    def click_dir(self):
        # get directory
        self.multi.mutex_sd_dir()
        self._update_listwidget()

    def click_cd(self):
        # change directory (move to child-dir)

        if not self.listWidget.currentItem():
            return

        # stop thread if running
        if self.multi and not self.multi.stopped:
            self.multi.stop()

        res = self.lnk.files.find_item(self.listWidget.currentItem().text())
        if res:
            self.lnk.sd_cd(res.filename)
            self._update_listwidget()

    def click_play(self):
        # play music

        # stop thread if running
        if self.multi and not self.multi.stopped:
            self.multi.stop()
            self.multi.wait()

        # stop music
        self.lnk.stop()

        items = self.listWidget.selectedItems()
        if len(items) == 1:
            # single
            res = self.lnk.files.find_item(self.listWidget.currentItem().text())
            if res:
                self.lnk.play(res.filename, display_name=res.dispname)
        else:
            # multi (run thread)
            dirlist = self.lnk.files.find_items([i.text() for i in items])
            self.multi.set_files(dirlist)
            self.multi.start()

    def click_stop(self):
        # stop music

        # stop thread if running
        if self.multi and not self.multi.stopped:
            self.multi.stop()

        print('')
        self.lnk.stop()


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
