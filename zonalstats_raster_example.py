class SubDomains( object ):
	'''
	rasterize subdomains shapefile to ALFRESCO AOI of output set
	'''
	def __init__( self, subdomains_fn, rasterio_raster, id_field, name_field, background_value=0, *args, **kwargs ):
		'''
		initializer for the SubDomains object

		The real magic here is that it will use a generator to loop through the 
		unique ID's in the sub_domains raster map generated.
		'''
		import numpy as np
		import rasterio

		self.subdomains_fn = subdomains_fn
		self.rasterio_raster = rasterio_raster
		self.id_field = id_field
		self.name_field = name_field
		self.background_value = background_value
		self._rasterize_subdomains( )
		self._get_subdomains_dict( )

	def _rasterize_subdomains( self ):
		'''
		rasterize a subdomains shapefile to the extent and resolution of 
		a template raster file. The two must be in the same reference system 
		or there will be potential issues. 

		returns:
			numpy.ndarray with the shape of the input raster and the shapefile
			polygons burned in with the values of the id_field of the shapefile

		gotchas:
			currently the only supported data type is uint8 and all float values will be
			coerced to integer for this purpose.  Another issue is that if there is a value
			greater than 255, there could be some error-type issues.  This is something that 
			the user needs to know for the time-being and will be fixed in subsequent versions
			of rasterio.  Then I can add the needed changes here.

		'''
		import geopandas as gpd
		import numpy as np

		gdf = gpd.read_file( self.subdomains_fn )
		id_groups = gdf.groupby( self.id_field ) # iterator of tuples (id, gdf slice)

		out_shape = self.rasterio_raster.height, self.rasterio_raster.width
		out_transform = self.rasterio_raster.affine

		arr_list = [ self._rasterize_id( df, value, out_shape, out_transform, background_value=self.background_value ) for value, df in id_groups ]
		self.sub_domains = arr_list
	@staticmethod
	def _rasterize_id( df, value, out_shape, out_transform, background_value=0 ):
		from rasterio.features import rasterize
		geom = df.geometry
		out = rasterize( ( ( g, value ) for g in geom ),
							out_shape=out_shape,
							transform=out_transform,
							fill=background_value )
		return out
	def _get_subdomains_dict( self ):
		import geopandas as gpd
		gdf = gpd.read_file( self.subdomains_fn )
		self.names_dict = dict( zip( gdf[self.id_field], gdf[self.name_field] ) )

def parallel_function( args, subs, statistic='mean', band=1 ):
	import numpy as np
	# unpack some args
	rasterio_raster = args
	rst = rasterio.open( rasterio_raster ).read( band )

	stats = {'mean':np.mean, 'min':np.min, 'max':np.max, 'sum':np.sum}
	try:
		stat = stats[ statistic ]
	except:
		BaseException( 'incorrect statistic name -- Try again.' )
	
	return {statistic:{ subs.names_dict[sub_domain[ sub_domain != background_value ].max()]:stat( rst[ sub_domain != background_value ] ) for sub_domain in subs.sub_domains }}
		
if __name__ == '__main__':
	import rasterio, os, json, glob
	import multiprocessing as mp
	from functools import partial
	import argparse

	# parser = argparse.ArgumentParser( description='program to compute data metrics from a directory of GeoTiffs' )
	# parser.add_argument( '-s', '--subdomains_fn', action='store', dest='subdomains_fn', type=str, help='path to shapefile to be used in computation. This is any file readable by geopandas.read_file(). ' )
	# parser.add_argument( '-t', '--template_raster_fn', action='store', dest='template_raster_fn', type=str, help='path to the template raster file. readable by rasterio.read().' )
	# parser.add_argument( '-id', '--id_field', nargs='?', const=1, default=None, action='store', dest='id_field', type=str, help='str name of the field to use in determining the id to represent subdomains in the shapefile when rasterized. ' )
	# parser.add_argument( '-name', '--name_field', nargs='?', const=1, default=None, action='store', dest='name_field', type=str, help='str name of the field to use in determining the name to represent subdomains in the shapefile when rasterized. ' )
	# parser.add_argument( '-o', '--out_json_fn', action='store', dest='out_json_fn', type=str, help='path to the json file to be generated with the output metrics' )
	# parser.add_argument( '-o', '--out_json_fn', action='store', dest='out_json_fn', type=str, help='path to the json file to be generated with the output metrics' )
	
	# # parse the arguments from the python commandline
	# args = parser.parse_args()

	# [TEST] here are some testing variables 
	template_raster_fn = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled/5ModelAvg/historical/tas/tas_mean_C_ar5_5ModelAvg_historical_12_2005.tif'
	subdomains_fn = '/workspace/Shared/Users/jschroder/ALFRESCO/SERDP/Domains/AOI_SERDP.shp'
	id_field = 'OBJECTID_1'
	name_field = 'Name'
	raster_path = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled/5ModelAvg/historical/tas'
	out_json_fn = '/workspace/Shared/Users/malindgren/test_json.json'
	# [TEST] END

	# # unpack to the collapsed variable names
	# subdomains_fn = args.subdomains_fn
	# template_raster_fn = args.template_raster_fn
	# id_field = args.id_field
	# name_field = args.name_field 
	rasterio_raster = rasterio.open( template_raster_fn )
	
	# hardwired for now. can change to make it more dynamic if needed.
	background_value = 0
	ncpus = 32
	statistic = 'mean'
	band = 1

	# compute the subdomains by burning each into its own raster band which matches the metadata of the template_raster_fn
	subs = SubDomains( subdomains_fn=subdomains_fn, rasterio_raster=rasterio_raster, id_field=id_field, name_field=name_field, background_value=0 )

	# now use this to compute the area / zonal statistics desired.
	f = partial( parallel_function, subs=subs, statistic=statistic, band=band )

	args_list = glob.glob( os.path.join( raster_path, '*.tif' ) ) # [WATCH ME] hardwired as geotiff only currently

	# [ TODO ] now we need to pull some kind of metadata 
	# [ TODO ] add the file_id_str to the args_list
	# 			pull from the filename or just use the base_filename...
	file_ids = [ os.path.basename(fn).split('.')[0] for fn in args_list ]

	pool = mp.Pool( ncpus )
	out = pool.map( f, args_list )
	pool.close()
	pool.join()

	# out = { file_id:i for file_id, i in zip(file_ids, out) }

	# # dump out as a json file for consumption later...
	# with open( out_json_fn, 'w' ) as file:
	# 	file.write( json.dumps( out ) )

	print( 'stats written to: {}'.format( out_json_fn ) )


	




