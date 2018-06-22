# how to rasterize a shapefile of polygons to a raster
import rasterio, fiona, os
from rasterio import features

# set up some filenames
rst_fn = '/home/malindgren/Documents/Julien/rasterize/raster_test_file.tif'
shp_fn = '/home/malindgren/Documents/Julien/rasterize/burn_shapes.shp'
output_fn = '/home/malindgren/Documents/Julien/rasterize/raster_test_file_burned.tif'

# # # # # FIONA EXAMPLE # # # # # # # 
# read in the shape and the raster
rst = rasterio.open( rst_fn )
shp = fiona.open( shp_fn )

# copy and update the metadata from the input raster for the output
meta = rst.meta
meta.update( compress='lzw' )

# now create the output and open and rasterize features and write it out
with rasterio.open( output_fn, 'w', **meta ) as out:
	out_arr = out.read( 1 )
	new = features.rasterize( shapes=( (i['geometry'], i['properties']['id']) for i in shp ), fill=0, out=out_arr, transform=out.transform )
	out.write_band( 1, new )



# # # # # # # GeoPANDAS EXAMPLE # # # # # # #
import geopandas as gpd

rst = rasterio.open( rst_fn )

# copy and update the metadata from the input raster for the output
meta = rst.meta
meta.update( compress='lzw' )

# open the ESRI Shapefile using geopandas read_file
shp_df = gpd.read_file( shp_fn )
# grab the geometry and id columns for the geoms and burn values
new = features.rasterize( ( (geom,value) for geom, value in zip( shp_df.geometry, shp_df.id ) ), fill=0, out=out_arr, transform=out.transform )

# now create the output and open and rasterize features and write it out
with rasterio.open( output_fn, 'w', **meta ) as out:
	out_arr = out.read( 1 )
	new = features.rasterize( ( (geom,value) for geom, value in zip( shp_df.geometry, shp_df.id ) ), fill=0, out=out_arr, transform=out.transform )
	out.write_band( 1, new )

