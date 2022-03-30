import time
import serial

ser = serial.Serial("/dev/ttyACM0", baudrate = 9600, parity=serial.PARITY_NONE, 
stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)


def print_text(text):
	ser.write(b'%s\n'%(text).encode())
	time.sleep(1)
	readedtext = ser.readline()
	print(readedtext)


