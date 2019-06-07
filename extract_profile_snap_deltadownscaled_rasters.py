# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# extract point profile from SNAP 2km data
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def list_data( path ):
	l = glob.glob(os.path.join( path, '*.tif' ))
	split_fn = [ os.path.basename(i).split('.')[0].split('_') for i in l ]

	if len( split_fn[0] ) == 7:
		colnames = ['variable', 'metric', 'units', 'model', 'scenario','month','year']	
	else:
		colnames = ['variable', 'metric', 'project', 'units', 'model', 'scenario','month','year']

	df = pd.DataFrame( split_fn, columns=colnames )
	df.month = df.month.astype(int)
	df.year = df.year.astype(int)
	df['fn'] = l
	out_df = df.sort_values(['year', 'month'])
	return out_df['fn'].tolist()

def extract_data( fn, row, col ):
	with rasterio.open( fn ) as rst:
		arr = rst.read(1)
	return arr[ row,col ]


if __name__ == '__main__':
	import os, glob, pyproj
	import numpy as np
	import rasterio
	from rasterio.features import rasterize
	import pandas as pd
	import multiprocessing as mp
	from shapely.geometry import Point
	from functools import partial
	lat,lon = (64.8378, -147.7164)
	point_name = 'Fairbanks'
	base_path = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled'
	output_path = '/workspace/Shared/Users/malindgren/pbienik_fairbanks_deltadownscaled'
	ncpus = 64
	groups = [('CRU-TS40', 'historical'),('NCAR-CCSM4', 'rcp85'),('GFDL-CM3','rcp85')]
	variables = ['tas','pr']
	
	for model, scenario in groups:
		print( model, scenario )
		data = dict()
		for variable in variables:
			print( variable )
			data_path = os.path.join( base_path, model, scenario, variable )
			
			# list/sort the files
			files = list_data( data_path )

			# make year_list
			years = int(files[0].split('.')[0].split('_')[-1]), int(files[-1].split('.')[0].split('_')[-1])

			# get template meta
			with rasterio.open( files[0] ) as tmp:
				meta = tmp.meta

			# project pt into 3338
			x,y = pyproj.Proj(meta['crs'].to_string())(lon,lat)

			# get the row col using the affine transform
			col, row = ~meta['transform'] * (x, y)
			col, row = int(col), int(row)

			# multiprocess
			f = partial(extract_data, row=row, col=col)
			pool = mp.Pool( ncpus )
			out = pool.map( f, files )
			pool.close()
			pool.join()
			
			dates = pd.date_range(str(years[0]), str(years[1]+1), freq='M')
			date_index = dates.map(lambda x: x.strftime('%Y-%m'))
			data[variable] = pd.DataFrame( out, index=date_index, columns=[variable] )

		# dump to disk as a csv with variables in the columns and time in the rows
		df = pd.concat( list( data.values() ), axis=1 )
		output_filename = os.path.join( output_path, '{}_{}_{}.csv'.format( model, scenario, point_name ) )
		df.to_csv( output_filename )



# # # # TEST THE LOCATION OF THE POINT:
# with rasterio.open( files[0] ) as tmp:
# 	meta = tmp.meta.copy()
# 	meta.update( compress='lzw' )
# 	arr = tmp.read(1)
# 	out_arr = np.zeros_like( arr )
# 	out_arr[ arr == -9999 ] = -9999
# 	out_arr[ row,col ] = 1

# 	with rasterio.open( '/workspace/Shared/Users/malindgren/pbienik_fairbanks_deltadownscaled/Fairbanks_location_point.tif', 'w', **meta ) as out:
# 		out.write( out_arr, 1 )