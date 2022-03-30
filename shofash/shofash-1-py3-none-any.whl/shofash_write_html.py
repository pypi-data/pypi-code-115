def shofash_write_html( filename, system, title, menu, content ):
	from .shofash_functions import skip_to_root
	
	# Replace the macros  	
	htmlOut = system				
	htmlOut = htmlOut.replace("{{{TITLE}}}",title)
	htmlOut = htmlOut.replace("{{{MENU}}}",menu)
	htmlOut = htmlOut.replace("{{{CONTENT}}}",content)
	htmlOut = htmlOut.replace("{{{ROOT}}}",skip_to_root(filename))
	
	# Finally write the file ...
	with open(filename, 'w') as file:
			print(filename)
			file.write(htmlOut)
