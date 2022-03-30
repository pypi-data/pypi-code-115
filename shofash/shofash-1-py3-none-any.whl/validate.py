#!/usr/bin/python3

import sys
import os
import time
from os.path import join, getsize, exists

def run():	

	sys.path.append(".") # Add in current directoy
	
	# Globals setup ____________________________________________________________
	
	froot = '.'
	ec = 0 # Number of errors
	
	for root, dirs, files in os.walk(froot,topdown = False):
		
		for name in files:
			if name.endswith("html"):
				f_txt = name[:-4] + "txt"
				file_txt = os.path.join(root,f_txt) # Long file name
				if not name == "index.html" and not os.path.exists(file_txt): # Now get the menu file menu.shofash
					file_html = os.path.join(root,name)
					ec = sayError( "No source file for " + file_html, ec)
		
	if ec == 1:
		print( "One error found")
	elif ec > 1:
		print( str(ec) + " errors found")
	else:
		print( "No errors found")
	
	return ec
