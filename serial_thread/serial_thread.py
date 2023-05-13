# coding: utf-8
import time
from PySide2 import QtCore


class SerialThread(QtCore.QThread):

    receiving = QtCore.Signal(str)

    def __init__(self, serial, parent=None):
        super().__init__(parent)
        self.mutex = QtCore.QMutex()
        self._stopped = True
        self._serial = serial
        self._rate = serial.baudrate

    def stop(self):
        with QtCore.QMutexLocker(self.mutex):
            self._stopped = True
        t = time.time()
        while self.isRunning():
            if (time.time() - t) > 2:
                self.receiving.emit('> thread terminate.')
                self.terminate()
            time.sleep(0.1)
        return True

    def scan(self):
        # read input buffer
        if self._serial.inWaiting():
            res = ''
            while self._serial.inWaiting():
                res += self._serial.read().decode('utf-8')
            return res

    def run(self):
        # thread main
        with QtCore.QMutexLocker(self.mutex):
            self._stopped = False

        while not self._stopped:
            res = self.scan()
            if res is not None:
                self.receiving.emit(res)
            time.sleep(0.1)
