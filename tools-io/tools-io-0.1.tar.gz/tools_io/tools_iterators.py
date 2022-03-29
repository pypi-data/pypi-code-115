#####################################################################################################################################################
#---------------------------------------------------------------------------------------------------------------------------------------------------#
#	- This file is a part 
#---------------------------------------------------------------------------------------------------------------------------------------------------#
#
#
#---------------------------------------------------------------------------------------------------------------------------------------------------#
#####################################################################################################################################################
#---------------------------------------------------------------------------------------------------------------------------------------------------#

#---------------------------------------------------------------------------------------------------------------------------------------------------#
#####################################################################################################################################################
#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Load essential packages:
import itertools
import warnings
import logging
#---------------------------------------------------------------------------------------------------------------------------------------------------#
#####################################################################################################################################################

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


#---------------------------------------------------------------------------------------------------------------------------------------------------#
def check_if_input_lists_are_valid( input_lists, instances_list ):
	if len( input_lists ) != len( instances_list ):
		raise ValueError( 'len( input_lists ) and len( instances_list ) must be the same but are: {} and {}.'.format( 
			len( input_lists ), len( instances_list ) 
			)
		)
	valid_lists = []
	for input_list, instances in zip( input_lists, instances_list ):
		valid_lists.append( check_if_list_is_valid( input_list, instances ) )
	return valid_lists
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def check_lengths_of_input_lists( input_lists ):
	list_lengths = [ len( input_list ) for input_list in input_lists ]
	if not check_if_all_elements_are_equal( list_lengths ):
		warnings.warn( 'input list do not have the same lengths, shorter lists will be padded with "None".' )
		max_length = max( list_lengths )
		#print( max_length )
		for input_list in input_lists:
			while len( input_list ) < max_length:
				input_list.append( None )
		#print( input_list )
	return input_lists
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def is_iterable( query ):
	try:
		iter( query )
	except TypeError:
		return False
	return True
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def check_if_list_is_valid( input_list, instances ):
	#is_iterable = is_iterable( input_list )
	if isinstance( input_list, str ) or not is_iterable( input_list ):
		log.info( 'input is either not iterable or a single string. The input gets turned into a list now.' )
		input_list = [ input_list ]
	if input_list and all( isinstance( x, instances ) for x in input_list ):
		return input_list
	else:
		raise TypeError( 'a list containing a {} - type object was passed, but list of {} was expected.'.format( type( input_list ), instances ) )
#---------------------------------------------------------------------------------------------------------------------------------------------------#
def check_if_all_elements_are_equal( iterable ):
	g = itertools.groupby(iterable)
	return next(g, True) and not next(g, False)
#---------------------------------------------------------------------------------------------------------------------------------------------------#