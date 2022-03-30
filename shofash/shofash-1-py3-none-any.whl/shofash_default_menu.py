def shofash_default_menu( path ): # Name of file including path
	from os.path import split as path_split
	from .shofash_functions import shofash_path_to_title

	path_split = path_split( path )
	dir = path_split[0]
	items = dir.split("/")
	levels = len(items) # Number of menu levels
	
	r = "<DIV CLASS='shofash_default_menu'>\n"
	
	for n in range(levels):
		if n > 0:
			r += " | "
			
		r += "<A HREF='" 
		section = items[n]
		
		down = levels - n - 1 # Number of "../" to add
		for x in range(down):
			r += "../"
			
		r += "index.html'>"
		if section == ".":
			r += "Home"
		else:
			r += shofash_path_to_title(section)
			
		r += "</a>"
		
		
	r += "</DIV>\n"
	
	return r
