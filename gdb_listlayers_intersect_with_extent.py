# PRAJNA DATA INTERSECT -- not fully tested

from shapely.geometry import Polygon, LineString
import fiona, os, itertools
import geopandas as gpd

gdb_fn = '/Users/malindgren/Documents/repos/prajna/RH_SampleData.gdb'
extent_fn = '/Users/malindgren/Documents/repos/prajna/extent.shp' # psuedo

# open the shapefile extent and get the geometry of the extent polygon
ext_df = gpd.read_file( extent_fn )
ext = ext_df.iloc[0][ 'geometry' ] # assumes its the first row in the dataframe

# get the layernames from the gdb
layernames = fiona.listlayers( gdb_fn )
layername = layernames[ 1 ]

# open and unlist the data in a single layer...  This may have to change depending on 
# how the footprints gdb is structured. May need another loop around the outside.
out = []
with fiona.open( gdb_fn, layer=layername ) as gdb:
	out = [ i for i in gdb ]
		f = next( i )
		out = out + [ f ]

# put the extracted GeoJSON-like records into a GeoDataFrame
gdf = gpd.GeoDataFrame.from_features( out )

# test the footprint geometries to your AOI geometry and return True / False
gdf[ 'intersects' ] = [ ext.intersects( geom ) for geom in gdf.geometry ]

# select all the rows that intersect your data
gdf_intersect_aoi = gdf[ gdf['intersects'] == True ]

# do other stuff with this information, like download the data that matches your AOI

