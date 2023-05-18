# coding: utf-8
import sys
import time
from PySide2.QtWidgets import (
    QPushButton, QApplication, QVBoxLayout, QDialog, QListWidget, QAbstractItemView)
from PySide2 import QtCore
from link4759.serial_link_4759 import Link4759


class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.multi = None
        # Create widgets
        self.listWidget = QListWidget()
        self.btnPlay = QPushButton("play")
        self.btnStop = QPushButton("stop")
        self.btnCd = QPushButton("change dir")
        self.btnDir = QPushButton("update widget(get dir)")
        # set selectionmode
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.listWidget)
        layout.addWidget(self.btnCd)
        layout.addWidget(self.btnPlay)
        layout.addWidget(self.btnStop)
        layout.addWidget(self.btnDir)
        # Set dialog layout
        self.setLayout(layout)
        self.btnCd.clicked.connect(self.click_cd)
        self.btnDir.clicked.connect(self.click_dir)
        self.btnPlay.clicked.connect(self.click_play)
        self.btnStop.clicked.connect(self.click_stop)
        # connect to 4759Player (& get directory list)
        self.lnk = Link4759()
        self.lnk.connect()
        self.lnk.sd_dir()
        self._update_listwidget()

    def _update_listwidget(self):
        # update listWidget items
        longnames = [l if l else f for f, l in self.lnk.files]
        self.listWidget.clear()
        self.listWidget.addItems(longnames)

    def _find_filename(self, name):
        # longname(?) -> filename
        for f, l in self.lnk.files:
            if name in (f, l):
                return f

    def closeEvent(self, event):
        if self.multi:
            self.multi.stop()
            self.multi.quit()
            self.multi.wait()
        self.lnk.stop()
        del self.lnk

    def click_dir(self):
        # get directory
        self.lnk.sd_dir()
        self._update_listwidget()

    def click_cd(self):
        # change directory (move to child-dir)
        filename = self._find_filename(self.listWidget.currentItem().text())
        if filename:
            self.lnk.sd_cd(filename)
            self._update_listwidget()

    def click_play(self):
        # play music

        # remove thread if running
        if self.multi and not self.multi.stopped:
            self.multi.stop()

        items = self.listWidget.selectedItems()
        if len(items) == 1:
            # single
            dispname = self.listWidget.currentItem().text()
            filename = self._find_filename(dispname)
            if filename:
                self.lnk.play(filename, display_name=dispname)
        else:
            # multi (run thread)
            dispnames = [i.text() for i in items]
            files = [(self._find_filename(l), l) for l in dispnames]
            if not self.multi:
                self.multi = PlayListThread(files, self.lnk, parent=self)
            else:
                self.multi.set_files(files)
            self.multi.start()

    def click_stop(self):
        # stop music

        # remove thread if running
        if self.multi and not self.multi.stopped:
            self.multi.stop()

        print('')
        self.lnk.stop()


class PlayListThread(QtCore.QThread):

    def __init__(self, files, lnk, parent=None, interval=5):
        QtCore.QThread.__init__(self, parent)
        self.mutex = QtCore.QMutex()
        self.stopped = False
        self.interval = interval
        self.lnk = lnk
        self.files = files

    def __del__(self):
        self.stop()
        self.quit()
        self.wait()

    def stop(self):
        # thread stop
        with QtCore.QMutexLocker(self.mutex):
            self.stopped = True

    def set_files(self, files):
        # set play list
        with QtCore.QMutexLocker(self.mutex):
            self.stopped = False
            self.files = files

    def run(self):
        # thread main (play in list)
        if not self.lnk or not self.files:
            return
        for filename, dispname in self.files:
            self.lnk.play(filename, display_name=dispname)
            t = time.time()
            while True:
                if self.stopped:
                    return
                info = self.lnk.play_state()
                if 'playing...' not in info:
                    break
                print('\r'+info.split('\n')[-2], end='')    # (play time)
                r = (time.time() - t) % self.interval
                time.sleep(self.interval - r)
            print('')


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
