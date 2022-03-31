# Setup the Directories
import os
from dir_ops import dir_ops as do

cwd_Dir = do.Dir( do.get_cwd() )

Dir = do.Path( os.path.abspath( __file__ ) ).ascend()   #Dir that contains the package 
src_Dir = Dir.ascend()                                  #src Dir that is one above
repo_Dir = src_Dir.ascend()                             #root Dir for the actual repository



