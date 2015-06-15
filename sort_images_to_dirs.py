# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
# script to copy and sort camera images to a new folder directory based on 
# DateTaken tags stored as EXIF tags in JPEG metadata.
#
# - to use this script you must install Pillow for python ( pip install Pillow )
#	everything else is a Python built-in.
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Michael Lindgren (malindgren@alaska.edu)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 

def get_exif( fn ):
	''' return EXIF tags from JPEG images using PIL as a dict '''
	ret = {}
	i = Image.open( fn )
	info = i._getexif()
	for tag, value in info.items():
			decoded = TAGS.get( tag, tag )
			ret[ decoded ] = value
	return ret

def split_datetime( dt ):
	''' split the dates and times from EXIF JPEG tags to datetime objects '''
	import datetime
	# split to dates and times
	d, t = dt.split( ' ' )
	date_list = d.split( ':' )
	# time_list = t.split( ':' )
	# convert to integer
	year, month, day = [ int(i) for i in date_list ]
	# hour, minute, second = [ int(i) for i in time_list ]
	# pass to a datetime object
	return datetime.datetime( year, month, day )

def dirs_from_datetime( output_dir, dt ):
	''' convert output_dir and python datetime object to a new folder path and make that folder '''
	new_dir = os.path.join( output_dir, dt.strftime( '%Y_%m_%d' ) )
	if not os.path.exists( new_dir ):
		os.makedirs( new_dir )
	return new_dir

if __name__ == '__main__':
	# read in some libraries
	import os, shutil, glob, datetime
	from PIL import Image
	from PIL.ExifTags import TAGS

	# directory where the images are stored -- Change these to windows pathing
	# NOTE the prefacing r to indicate raw string due to Windows slashes.
	input_dir = r'C:\Users\malindgren\Documents\restumpedonavbscript'
	output_dir = r'C:\Users\malindgren\Documents\restumpedonavbscript\outputs'
	log_filename = os.path.join( output_dir, 'log_error_files.txt' )

	# list all of the data in the input directory with extension .jpg 
	#	this uses a simple regex pattern to return both upper and lower case extensions
	jpegs = glob.glob( os.path.join( input_dir, '*.[jJ][pP][gG]' ) )

	# create a log file for retention of error files
	log = open( log_filename, 'w' )
	
	# loop through the files and store the DateTime EXIF tag as a python datetime object
	fn_datetime = {} # make an empty dict to hold output
	for jpg in jpegs:
		# condition to test if jpg has EXIF tags
		if Image.open(jpg)._getexif() != None:
			fn_datetime[ jpg ] = split_datetime( get_exif( jpg )[ 'DateTime' ] )
		else:
			# if there are no tags, log the filename as a problem file
			log.writelines( jpg + '\n' )

	log.close() # close the log file

	# now lets find all of the unique dates and make folders for the outputs
	unique_dates = set( fn_datetime.values() )

	# lets create our needed output directories in the output_dir
	new_dirs = [ dirs_from_datetime( output_dir, dt ) for dt in unique_dates ]

	# now lets fill em with the images
	[ shutil.copy( fn, os.path.join( output_dir, dt.strftime( '%Y_%m_%d' ), os.path.basename( fn ) ) ) for fn, dt in fn_datetime.iteritems() ]

	# finally lets copy those problem files to a problem directory in the output_dir
	log = open( log_filename, 'r' )
	problems = log.read().splitlines()
	log.close()

	# make a new directory to hold the problems if one does not already exist
	problem_dir = os.path.join( output_dir, 'problem_files' )
	if not os.path.exists( problem_dir ):
		os.makedirs( problem_dir )

	# move em to problem_dir
	[ shutil.copy( fn, os.path.join( output_dir, problem_dir ) ) for fn in problems ]




