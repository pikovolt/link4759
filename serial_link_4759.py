# coding: utf-8
import re
import time
import serial
from serial.tools import list_ports

ptnFilename = r'^((\.{2})|((?!\.).{1,8}(\.vgm|\.s98)*))\s+(\d+|<dir>)\s{2}\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2}(\s.*)*'


class Link4759():

  def __init__(self):
    self.files = []
    self.ser = serial.Serial()

  def __del__(self):
    self.disconnect()

  def _get_dir_list(self, cmd):
    # (change current-directory or get directory-list)
    self.ser.reset_input_buffer()
    msg = send_cmd(cmd, self.ser)

    # Update file list from response string
    try:
      # search elements matching pattern (get the first 12 characters)
      _flist = [l[:12].strip() for l in msg.split('\n') \
                if re.search(ptnFilename, l, re.I)]
    except:
      _flist = []
    finally:
      if _flist:
        _flist = [''.join(f.split()) for f in _flist]   #(delete white-space)
        self.files = _flist

  def help(self):
    # print help
    send_cmd('help', self.ser)

  def sd_dir(self):
    # print current dirctory (& update files)
    cmd = 'sd dir'
    self._get_dir_list(cmd)

  def sd_cd(self, dirname):
    # change dirctory (on SD-Card)
    name = find_name(dirname, self.files)
    _dirname = name if name else dirname
    cmd = 'cd %s' % _dirname
    self._get_dir_list(cmd)

  def play_state(self):
    # get play state
    return send_cmd('play', self.ser, silent=True)

  def play_list(self, filenames, interval=5.0):
    # play list (at current dirctory)
    for filename in filenames:
      self.play(filename)
      while True:
        time.sleep(interval)
        info = self.play_state()
        if 'Not playing' in info:
          break
        print('\r'+info.split('\n')[-2], end='')
      print('')

  def play(self, filename):
    # play music
    name = find_name(filename, self.files)
    _fname = name if name else filename
    send_cmd('play %s' % _fname, self.ser)

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
      self.ser.open()
      print('%s, %dbaud linked.' % (self.ser.port, baudrate))

  def disconnect(self):
    # disconnect serial connection to 4759Player
    print('%s close.' % (self.ser.port))
    try:
      self.ser.close()
    except:
      pass

  def print_files(self):
    # print directory list
    print('-'*12)
    for i in self.files:
      print(i)
    print('-'*12)


def find_name(keyword, files):
  # Find names containing strings
  _names = []
  for f in files:
    if keyword in f:
      _names.append(f)
  if len(_names) == 1:
    return _names[0]

  if _names:
    print('-'*12)
    for f in _names:
      print(f)
    print('-'*12)


def wait_msg(ser):
  # before recive wait
  s = ser.inWaiting()
  while ser.inWaiting() == s:
    time.sleep(0.1)

  # receiving wait
  dif = True
  while dif:
    s = ser.inWaiting()
    time.sleep(0.1)
    dif = (s < ser.inWaiting())


def send_cmd(cmd, ser, silent=False):
  # send command
  ser.write((cmd+'\r').encode('utf-8'))
  return print_recv(ser, silent)


def print_recv(ser, silent=False):
  # get response (& print)
  msg = ''
  wait_msg(ser)
  while ser.inWaiting() > 0:
    msg += ser.read().decode('utf-8')
  if not silent:
    print(msg)
  return msg


def examples():
  from link4759.serial_link_4759 import Link4759

  lnk = Link4759()

  # connect to 4759player
  lnk.connect()

  # print current dir
  lnk.sd_dir()

  # print current file(or dir) list
  lnk.files_print()

  # change current dir
  lnk.sd_cd('foo')

  # play music (input filename)
  lnk.play('01_bar.vgm')

  # play music (input keyword)
  lnk.play('01')

  # stop music
  lnk.stop()

  # disconnect to 4759player
  lnk.disconnect()
