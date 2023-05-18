# coding: utf-8
import re
import time
import serial
from serial.tools import list_ports

# target names: '..' or filename(8character) + (.vgm|.s98|.mdx)
ptnFilename = r'^(?P<filename>((\.{2})|((?!\.).{1,11}(\.vgm|\.s98|\.mdx)*)))\s+(\d+|<dir>)\s{2}\d{4}/\d{2}/\d{2}\s\d{2}:\d{2}:\d{2}(\s+(?P<longname>.*))*'

class Link4759():

  def __init__(self, timeout=2):
    self.files = []
    self.ser = serial.Serial(timeout=timeout)

  def __del__(self):
    self.disconnect()

  def _get_dir_list(self, cmd):
    # (change current-directory or get directory-list)
    msg = send_cmd(cmd, self.ser)

    # Update file list from response string
    try:
      _flist = []
      for l in msg.split('\n'):
        m = re.search(ptnFilename, l, re.I)
        if m:
          fname = ''.join(m.group('filename').split())  #(delete white-space)
          lname = m.group('longname')
          _flist.append((fname, lname))
    except:
      _flist = []
    finally:
      if _flist:
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
    for filename, longname in filenames:
      self.play(filename)
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
    name = find_name(filename, self.files)
    _fname = name if name else filename
    silent = False if display_name is None else True
    send_cmd('play %s' % _fname, self.ser, silent=silent)
    if silent:
      print('play %s\n-' % display_name)

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
    for i in self.files:
      print(i)
    print('-'*12)

  def send(self, cmd, silent=False):
    # send command
    send_cmd(cmd, self.ser, silent)


def port_open(ser, chalenge=5, interval=2):
  # serial port open (chalenge 5 time, interval 2sec)
  for i in range(chalenge):
    try:
      ser.open()
      if ser.is_open:
        return True
    except serial.serialutil.SerialException as e:
      print(e)
    if i < chalenge:
      time.sleep(interval)
  return False


def find_name(keyword, files):
  # Find names containing strings
  _names = []
  for filename, longname in files:
    if keyword in filename:
      _names.append(filename)
  if len(_names) == 1:
    return _names[0]

  if _names:
    print('-'*12)
    for f in _names:
      print(f)
    print('-'*12)


def send_cmd(cmd, ser, silent=False):
  # send command
  ser.reset_input_buffer()
  ser.write((cmd+'\r').encode('utf-8'))
  return print_recv(ser, silent)


def print_recv(ser, silent=False):
  # get response (& print)
  msg = ''
  time.sleep(0.5)
  while ser.inWaiting() > 0:
    msg += ser.read().decode('utf-8')
  if not silent:
    print(msg)
  return msg


def examples():
  from serial_link_4759 import Link4759

  lnk = Link4759()

  # connect to 4759player
  lnk.connect()

  # print current dir
  lnk.sd_dir()

  # print current file(or dir) list
  lnk.files_print()

  # print help
  lnk.help()

  # send command
  lnk.send('fm')

  # change current dir
  lnk.sd_cd('foo')

  # play music (input filename)
  lnk.play('01_bar.vgm')
  lnk.play('02_foobar.vgm')

  # play music (input keyword)
  lnk.play('01')
  lnk.play('02')

  # play music (name-list)
  lnk.play(lnk.files[1:])
  lnk.play(['01', '02'])

  # stop music
  lnk.stop()

  # disconnect to 4759player
  lnk.disconnect()
