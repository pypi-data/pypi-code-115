import os
from pathlib import Path

def auto_create_folder( default_path = Path( os.environ[ 'USERPROFILE' ], "Desktop" ), folder_extend = None ):
    default_path = Path( default_path )
    default_list = str( default_path ).split( "\\" )
    default_list.remove( "" )
    print( default_list )

    folder_path = Path( default_path, folder_extend )
    folder_list = str( folder_path ).split( "\\" )
    print( folder_list )

    ##remove default path from full path
    for def_folder in default_list:
        folder_list.remove( def_folder )

    print( len( folder_list ) )
    print( folder_list )


    increment_path = default_path
    for folder in folder_list:
        increment_path = Path( increment_path, folder )
        print( increment_path )

        if os.path.isdir( increment_path ) == False:
            os.mkdir( increment_path )

        else:
            print( "Directory already exists." )
            pass

auto_create_folder( default_path = "C:/", folder_extend = "level_a/level_b/level_c" )
