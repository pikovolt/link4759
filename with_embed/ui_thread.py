# coding: utf-8
import time
from PySide2 import QtCore


class PlayListThread(QtCore.QThread):

    dbg_rot = [
        '.    ',
        ' .   ',
        '  .  ',
        '   . ',
        '    .',
        '   . ',
        '  .  ',
        ' .   ']

    def __init__(self, files, lnk, parent=None, interval=2.5):
        super(PlayListThread, self).__init__(parent)
        self.mutex = QtCore.QMutex()
        self.stopped = True
        self.interval = interval
        self.lnk = lnk
        self.files = files
        self._cmd = None

    def rot(self, cnt):
        # print rotator (for debug)
        print('\r'+self.dbg_rot[cnt % 8], end='', flush=True)

    def playtime(self, t):
        # print playtime (for debug)
        print(f'{int(t / 60):02}:{int(t % 60):02}\r', end='', flush=True)

    def run(self):
        # thread main (play in list)
        if not self.lnk or not self.files.items:
            return
        with QtCore.QMutexLocker(self.mutex):
            self.stopped = False

        for i in self.files.items:
            if not i.is_dir:
                self.mutex_play(i.filename, display_name=i.dispname)

            t = time.time()
            cnt = 0
            while True:
                if self._cmd == 'next':
                    print('\rPlay list (Next).')
                    self._cmd = None
                    break
                if self._cmd == 'stop' or self.stopped:
                    self.stop()     # (change status)
                    print('\rPlay list terminated.')
                    return

                self.rot(cnt); cnt+=1; self.playtime(time.time() - t)   # (for debug)
                info = self.mutex_play_state()
                if 'playing...' not in info:
                    break

                r = (time.time() - t) % self.interval
                time.sleep(self.interval - r)

            print('\r', end='')
        print('Play list finished.')
        self.stop()     # (change status)

    # (with mutex functions)
    def cmd(self, cmd):
        # thread stop
        with QtCore.QMutexLocker(self.mutex):
            self._cmd = cmd

    # (with mutex functions)
    def stop(self):
        # thread stop
        with QtCore.QMutexLocker(self.mutex):
            self.stopped = True

    def set_files(self, files):
        # set play list
        with QtCore.QMutexLocker(self.mutex):
            self.stopped = False
            self.files = files

    def mutex_send(self, cmd):
        # send command (with mutex lock)
        with QtCore.QMutexLocker(self.mutex):
            self.lnk.send(cmd)

    def mutex_play(self, filename, display_name=None):
        # play (with mutex lock)
        with QtCore.QMutexLocker(self.mutex):
            self.lnk.play(filename, display_name)

    def mutex_play_state(self):
        # play_state (with mutex lock)
        with QtCore.QMutexLocker(self.mutex):
            return self.lnk.play_state()

    def mutex_sd_dir(self):
        # list directory & update files (with mutex lock)
        with QtCore.QMutexLocker(self.mutex):
            return self.lnk.sd_dir()

    def mutex_sd_cd(self, filename):
        # change directory (with mutex lock)
        with QtCore.QMutexLocker(self.mutex):
            return self.lnk.sd_cd(filename)
