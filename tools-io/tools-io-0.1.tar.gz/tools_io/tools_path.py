

import os
import warnings
import logging
#---------------------------------------------------------------------------------------------------------------------------------------------------#
#####################################################################################################################################################

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

#---------------------------------------------------------------------------------------------------------------------------------------------------#
def make_output_path( query_path, output_path, overwrite = False ):
	if '.' not in output_path:
		raise ValueError( 'The output path: {} is not valid because it does not specify the file extension!'.format( output_path ) )
	if query_path in (None, ''):
		query_path = output_path
	else:
		output_path = query_path
	if not overwrite:
		file_extension = '.' + query_path.rsplit('.')[1]
		index = 0
		while os.path.exists( output_path ):
			index += 1
			if index > 1:
				replace_extension = '_{}'.format( index - 1 ) + file_extension
			else:
				replace_extension = file_extension
			output_path = output_path.replace( replace_extension, '_{}{}'.format( index, file_extension ) )
	log.info( 'Saving file to {}'.format( output_path ) )
	if not os.path.exists( os.path.dirname( output_path ) ) and  os.path.dirname( output_path ) not in ( '', ' ', None ):
		os.mkdir( os.path.dirname( output_path ) )
		log.info( 'Output directory {} did not exist and was created.'.format( os.path.dirname( output_path ) ) )
	return output_path
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def make_output_dir( query_dir, output_dir ):
	if '.' in output_dir:
		raise ValueError( 'The output dir: {} is not valid because it contains a dot!'.format( output_dir ) )
	if query_dir in ( None, '', ' ' ):
		query_dir = output_dir
	else:
		output_dir = query_dir
	index = 0
	output_dir_index = output_dir + '_0'
	while os.path.exists( output_dir ):
		index += 1
		output_dir = output_dir_index.replace( '_0', '_{}'.format( index ) )
	log.info( 'Saving file to {}'.format( output_dir ) )
	if not os.path.exists( output_dir ) :
		os.mkdir( output_dir )
		log.info( 'Output directory {} did not exist and was created.'.format( output_dir ) )
	return output_dir
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def append_before_extension( file_path: str, string: str ):
	name, ext = os.path.splitext( file_path )
	return '{name}_{string}{ext}'.format( name = name, string = string, ext = ext )
#---------------------------------------------------------------------------------------------------------------------------------------------------#