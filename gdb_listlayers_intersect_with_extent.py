# * * * * * * * * * * * * * * * * * * 
# ABOVE FOOTPRINT INTERSECT
# * * * * * * * * * * * * * * * * * * 
def open_layer( fn, layer ):
	''' opens the gdb layer and returns the first row '''
	with fiona.open( gdb_fn, layer=layername ) as c:
		dat = next( c )
	return dat

if __name__ == '__main__':
	from shapely.geometry import Polygon, LineString
	import fiona, os, itertools
	import geopandas as gpd

	gdb_fn = '/Users/malindgren/Documents/repos/prajna/RH_SampleData.gdb'
	extent_fn = '/Users/malindgren/Documents/repos/prajna/extent.shp' # psuedo

	# open the shapefile extent and get the geometry of the extent polygon
	ext_df = gpd.read_file( extent_fn )
	ext = ext_df.iloc[0][ 'geometry' ] # assumes first row in df is extent poly

	# get the layernames from the gdb
	layernames = fiona.listlayers( gdb_fn )

	# get the first row from each layer...
	gdf = gpd.GeoDataFrame.from_features([ open_layer( fn, layername ) for layername in layernames[1:3] ])

	# # make a layer into the geodataframe
	# gdf = gpd.read_file( fn, layer=layername )

	# test the footprint geometries to your AOI geometry and return True / False
	gdf[ 'intersects' ] = [ ext.intersects( geom ) for geom in gdf.geometry ]

	# select all the rows that intersect your data
	gdf_intersect_aoi = gdf[ gdf['intersects'] == True ]


# * * * * * * OLD ACCESS METHOD * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
# # open and unlist the data in a single layer...  This may have to change depending on 
# # how the footprints gdb is structured. May need another loop around the outside.
# out = []
# with fiona.open( gdb_fn, layer=layername ) as gdb:
# 	out = [ i for i in gdb ]
# 		f = next( i )
# 		out = out + [ f ]

# # put the extracted GeoJSON-like records into a GeoDataFrame
# gdf = gpd.GeoDataFrame.from_features( out )
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *