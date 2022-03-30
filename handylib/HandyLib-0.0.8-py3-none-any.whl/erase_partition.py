import sys
import os
import struct
def write_0(path,b_size):
	print('start writing 0...')
	write_data(path,b_size,b'0')

def write_1(path,b_size):
	print('start writing 1...')
	write_data(path,b_size,b'1')

def write_data(path,b_size,data ):
	path = os.path.join(path,'temp_file.txt')
	try:
		os.remove(path)
	except:
		pass
	f = open(path, 'wb')
	while True:
		try:
			f.write(data*b_size)
		except Exception as e:
			if b_size>1:
				b_size = int(b_size/2)
				if b_size==0:
					b_size = 1
			if b_size == 1:
				return
	try:
		os.remove(path)
	except:
		pass

def erase_all_files(path):
	fs = os.listdir(path)
	for i in fs:
		try:
			os.remove(os.path.join(path,i))
		except:
			pass
		try:
			os.removedirs(os.path.join(path,i))
		except:
			pass
def erase_disk(path, num=1,b_size=4096):
	print('erase ' + path + ' ' + str(num) + ' times')
	erase_all_files(path)
	for i_num in range(num):
		write_0(path,b_size)
		write_1(path,b_size)
	erase_all_files(path)
	