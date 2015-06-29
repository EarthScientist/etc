# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# this is a simple testing script to see what I can do with the Xray library and the type of time series data we use 
# at snap.  This is just a set of simple things I have had success with.
#
# Michael Lindgren malindgren@alaska.edu
#
# LICENSE: MIT
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def coordinates( fn ):
	'''
	take a raster file as input and return the centroid coords for each 
	of the grid cells as a pair of numpy 2d arrays (longitude, latitude)
	'''
	import rasterio
	import numpy as np
	from affine import Affine
	from pyproj import Proj, transform

	# Read raster
	with rasterio.open(fn) as r:
		T0 = r.affine  # upper-left pixel corner affine transform
		p1 = Proj(r.crs)
		A = r.read_band(1)  # pixel values

	# All rows and columns
	cols, rows = np.meshgrid(np.arange(A.shape[1]), np.arange(A.shape[0]))

	# Get affine transform for pixel centres
	T1 = T0 * Affine.translation(0.5, 0.5)
	# Function to convert pixel row/column index (from 0) to easting/northing at centre
	rc2en = lambda r, c: (c, r) * T1

	# All eastings and northings (there is probably a faster way to do this)
	eastings, northings = np.vectorize(rc2en, otypes=[np.float, np.float])(rows, cols)

	# Project all longitudes, latitudes
	# longs, lats = transform(p1, p1.to_latlong(), eastings, northings)
	# return longs, lats
	return eastings, northings

if __name__ == '__main__':
	import os, rasterio, xray
	import pandas as pd
	import numpy as np

	# filename
	fn = '/Users/malindgren/Documents/snap_data_test/tas_mean_C_alf_cru_TS31_07_1901_2009.tif'
	
	# read in the data using rasterio to a numpy ndarray
	data = rasterio.open( fn ).read()

	# lets make a time dimension that matches this particuar data which is all Julys for a period of years
	times = pd.date_range( '1901', '2010', freq='A-JUL' )

	# get a meshgrid of the input lons and lats.
	lons, lats = coordinates( fn )

	# the only odd thing here is that there could be some issues with the lats / lons that needs sorting. 
	# Potentially due to the number of unique lat longs in projected space to what is expected based on the coordinates of the numpy ndarrays....
	new_arr = xray.DataArray( data, coords=( times, np.unique(lats),np.unique(lons)), dims=('time', 'lat', 'lon'), name=None, attrs=None )

	# now we can slice by the time dimension like this
	time_1921 = new_arr.loc[ '1921' ]

	# or groupby decades like this
	# add a new variable and set it with the decades as the index
	new_arr[ 'month_start' ] = ('time', ((times.year//10) *10) )

	# use the new variable name to group by
	decades = new_arr.groupby( 'month_start' )

	# this is a potential way to perform a decadal mean calculation using the xray DataArray
	decadal_means = new_arr.groupby( 'month_start' ).mean( 'time' )

	# this is something that we should look at for ALFRESCO Processing as well: dask arrays
	# import dask.array as da
	# In [351]: tmp = da.from_array( data, chunks=(1000,10000) )

	# In [352]: %timeit tmp + tmp
	# 10 loops, best of 3: 29.1 ms per loop

	# In [353]: %timeit data + data
	# 1 loops, best of 3: 764 ms per loop
