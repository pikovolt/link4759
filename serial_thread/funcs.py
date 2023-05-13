# coding: utf-8
import time
import serial


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


def send_cmd(cmd, ser, silent=False):
    # send command
    ser.reset_input_buffer()
    ser.write((cmd+'\r').encode('utf-8'))
    res = print_recv(ser, silent)
    return res


def print_recv(ser, silent=False):
    # get response (& print)
    msg = ''
    time.sleep(0.5)
    while ser.inWaiting() > 0:
        msg += ser.read().decode('utf-8')
    if not silent:
        print(msg)
    return msg
