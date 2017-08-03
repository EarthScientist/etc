# # # # # # # # #
# # super-simple CLI tool to crop/clip raster using a shapefile with rasterio
# # # # # # # # #
def clip_raster( rst_fn, shp_fn, out_fn ):
    '''
    take input raster and shapefile in the same
    CRS (strict) and output a raster clipped / cropped
    to the shapefile shape domain. The idea is to use
    a shapefile with only a single extent shape, but may
    work for multiples...

    ARGUMENTS:
    ----------
    rst_fn: [str] path to the GeoTiff to clip
    shp_fn: [str] path to the shapefile containing masking polygon(s)
    out_fn: [str] path to dump the clipped raster (will be overwritten)

    RETURNS:
    --------
    out_fn with the side-effect of writing a clipped GeoTiff file to disk with
    LZW compression. 

    '''
    import fiona
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import reproject, Resampling

    # shapefile work
    with fiona.open( shp_fn, "r") as shapefile:
        features = [ feature["geometry"] for feature in shapefile ]

    # input raster work
    with rasterio.open( rst_fn ) as src:
        out_image, out_transform = mask( src, features, crop=True )
        out_meta = src.meta.copy()

    # output raster work
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform,
                     "compress": "lzw"})

    with rasterio.open(out_fn, "w", **out_meta) as dst:
        dst.write( out_image )

    return out_fn

if __name__ == '__main__':
    import argparse

    # parse the commandline arguments
    parser = argparse.ArgumentParser( description='clip raster to the shape(s) included in a shapefile. both must be in the same crs.' )
    parser.add_argument( "-r", "--rst_fn", action='store', dest='rst_fn', type=str, help="path to the GeoTiff file to be clipped/cropped." )
    parser.add_argument( "-s", "--shp_fn", action='store', dest='shp_fn', type=str, help="path to the polygon Shapefile to be used as clip/crop extent." )
    parser.add_argument( "-o", "--out_fn", action='store', dest='out_fn', type=str, help="path to the output GeoTiff to be created. existing will be overwritten." )
    
    args = parser.parse_args()
    rst_fn = args.rst_fn
    shp_fn = args.shp_fn
    out_fn = args.out_fn

    print( clip_raster( rst_fn, shp_fn, out_fn ) )
    