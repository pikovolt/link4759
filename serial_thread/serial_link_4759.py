# coding: utf-8
import re
import time
import serial
from serial.tools import list_ports
from link4759.serial_thread.funcs import port_open, send_cmd
from link4759.serial_thread.dir_item import DirList

# target names: '..' or filename(8character) + (.vgm|.s98|.mdx)
ptnFilename = r'^(?P<filename>((\.{2})|((?!\.).{1,11}(\.vgm|\.s98|\.mdx)*)))\s+(?P<size_type>(\d+|<dir>))\s{2}\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2}(\s+(?P<longname>.*))*'


class Link4759():

    def __init__(self, timeout=0.5):
        self.files = DirList()
        self.ser = serial.Serial(timeout=timeout)

    def __del__(self):
        self.disconnect()

    def _get_dir_list(self, cmd):
        # (change current-directory or get directory-list)
        msg = send_cmd(cmd, self.ser)

        # Update file list from response string
        try:
            dirlist = DirList()
            for l in msg.split('\n'):
                m = re.search(ptnFilename, l, re.I)
                if m:
                    fname = ''.join(m.group('filename').split())  #(delete white-space)
                    lname = m.group('longname')
                    size_type = m.group('size_type')
                    dirlist.add(fname, lname, size_type)
        except:
            dirlist = DirList()
        finally:
            self.files = dirlist

    def help(self):
        # print help
        send_cmd('help', self.ser)

    def sd_dir(self):
        # list directory & update files
        self._get_dir_list('sd dir')

    def sd_cd(self, dirname):
        # change dirctory (on SD-Card)
        res = self.files.find_item(dirname)
        if not res:
            # (retry..)
            self.sd_dir()
            res = self.files.find_item(dirname)
        if res:
            if res.is_dir:
                self._get_dir_list('cd %s' % res.filename)

    def play_state(self):
        # get play state
        return send_cmd('play', self.ser, silent=True)

    def play_list(self, filenames, interval=5.0):
        # play list (at current dirctory)
        for i in filenames:
            if i.is_dir:
                continue
            self.play(i.filename)
            t = time.time()
            while True:
                r = (time.time() - t) % interval
                time.sleep(interval - r)
                info = self.play_state()
                if 'playing...' not in info:
                    break
                print('\r'+info.split('\n')[-2], end='')  # (play time)
            print('')
        print('play list loop finished.')

    def play(self, filename, display_name=None):
        # play music
        res = self.files.find_item(filename)
        if res and not res.is_dir:
            send_cmd('play %s' % res.filename, self.ser, silent=True)
            print('play %s\n-' % res.dispname)

    def stop(self):
        # stop music
        send_cmd('stop', self.ser)

    def connect(self, port_name=None, baudrate=9600):
        # connect serial connection to 4759Player
        devices = [info.device for info in list_ports.comports()]
        if (not devices and port_name is None) or (port_name is not None and port_name not in devices):
            print('COM port not found.')
            print(' - devices:', devices)
        else:
            self.ser.port = devices[0] if port_name is None else port_name
            self.ser.baudrate = baudrate
            if not port_open(self.ser):
                print('COM port(%s) could not open.' % self.ser.port)
            else:
                print('%s, %dbaud linked.' % (self.ser.port, baudrate))

    def disconnect(self):
        # disconnect serial connection to 4759Player
        try:
            if not self.ser.is_open:
                print('%s closed.' % (self.ser.port))
            else:
                self.ser.close()
                if not self.ser.is_open:
                    print('%s closed.' % (self.ser.port))
        except Exception as e:
            print(e)

    def print_files(self):
        # print directory list
        print('-'*12)
        for i in self.files.items:
            print(i)
        print('-'*12)

    def send(self, cmd, silent=False):
        # send command
        send_cmd(cmd, self.ser, silent)
