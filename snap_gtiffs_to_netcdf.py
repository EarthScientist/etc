# # # # # #
# Make NetCDF data from our SNAP data GeoTiffs for app-development.
# # # # # # 
def open_raster( fn, band=1 ):
    with rasterio.open( fn ) as out:
        arr = out.read( band )
    return arr

def coordinates( fn=None, meta=None, numpy_array=None, input_crs=None, to_latlong=False ):
    '''
    take a raster file as input and return the centroid coords for each 
    of the grid cells as a pair of numpy 2d arrays (longitude, latitude)
    User must give either:
        fn = path to the rasterio readable raster
    OR
        meta & numpy ndarray (usually obtained by rasterio.open(fn).read( 1 )) 
        where:
        meta = a rasterio style metadata dictionary ( rasterio.open(fn).meta )
        numpy_array = 2d numpy array representing a raster described by the meta
    input_crs = rasterio style proj4 dict, example: { 'init':'epsg:3338' }
    to_latlong = boolean.  If True all coordinates will be returned as EPSG:4326
                         If False all coordinates will be returned in input_crs
    returns:
        meshgrid of longitudes and latitudes
    borrowed from here: https://gis.stackexchange.com/a/129857
    ''' 
    
    import rasterio
    import numpy as np
    from affine import Affine
    from pyproj import Proj, transform

    if fn:
        # Read raster
        with rasterio.open( fn ) as r:
            T0 = r.affine  # upper-left pixel corner affine transform
            p1 = Proj( r.crs )
            A = r.read( 1 )  # pixel values

    elif (meta is not None) & (numpy_array is not None):
        A = numpy_array
        if input_crs != None:
            p1 = Proj( input_crs )
            T0 = meta[ 'affine' ]
        else:
            p1 = None
            T0 = meta[ 'affine' ]
    else:
        BaseException( 'check inputs' )

    # All rows and columns
    cols, rows = np.meshgrid(np.arange(A.shape[1]), np.arange(A.shape[0]))
    # Get affine transform for pixel centres
    T1 = T0 * Affine.translation( 0.5, 0.5 )
    # Function to convert pixel row/column index (from 0) to easting/northing at centre
    rc2en = lambda r, c: ( c, r ) * T1
    # All eastings and northings -- this is much faster than np.apply_along_axis
    eastings, northings = np.vectorize(rc2en, otypes=[np.float, np.float])(rows, cols)

    if to_latlong == False:
        return eastings, northings
    elif (to_latlong == True) & (input_crs != None):
        # Project all longitudes, latitudes
        longs, lats = transform(p1, p1.to_latlong(), eastings, northings)
        return longs, lats
    else:
        BaseException( 'cant reproject to latlong without an input_crs' )


if __name__ == '__main__':
    # stack GTiff to NetCDF
    import os, glob, rasterio, itertools
    import numpy as np
    import xarray as xr
    import pandas as pd

    # base_path = '/Data/Base_Data/Climate/AK_CAN_2km_v2_1'
    base_path = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled'

    # models = ['5ModelAvg','GFDL-CM3','GISS-E2-R','IPSL-CM5A-LR','MRI-CGCM3','NCAR-CCSM4']
    models = ['ts40']

    scenarios = [ 'historical', 'rcp85' ]
    variable = 'rsds'

    for model, scenario in itertools.product( models, scenarios ):
        print( model, scenario )
        # list em
        cur_path = os.path.join( base_path, model, scenario, variable )
        files = glob.glob( os.path.join( cur_path, '*.tif' ) )
        out_fn = os.path.join('/workspace/Shared/Users/malindgren/snap_netcdf_testing/akcan_2km',model,scenario,variable,'{}_{}_{}.nc'.format(variable, model,scenario) )
        try:
            dirname = os.path.dirname( out_fn )
            if not os.path.exists( dirname ):
                os.makedirs( dirname )
        except:
            pass

        # break up filename attrs
        break_names = [ os.path.basename(fn).split('.')[0].split('_') for fn in files ]
        colnames = ['variable', 'metric', 'units', 'group', 'model', 'scenario', 'month', 'year']

        # make a df and make sure they are chronological
        df = pd.DataFrame(break_names, columns=colnames )
        df['fn'] = files
        df = df.sort_values(['year', 'month']).reset_index()

        # make a list from it...
        files = df.fn.tolist()

        # list and stack em...
        arr = np.dstack([ open_raster(fn) for fn in files ])

        # get the coordinates as a meshgrid
        x,y = coordinates( fn=df.fn.iloc[0] )
        begin = df.iloc[0].year
        end = str(int(df.iloc[-1].year) + 1)
        time = pd.date_range( begin, end, freq='M' )
        variable = df.variable.iloc[0]

        new_ds = xr.Dataset({variable: (['x', 'y', 'time'], arr)},
                        coords={'projection_x_coordinates': (['x', 'y'], x),
                                'projection_y_coordinates': (['x', 'y'], y),
                                'time':time })

        # write it back out to disk with compression encoding
        encoding = new_ds[ variable ].encoding
        encoding.update( zlib=True, complevel=5, contiguous=False, chunksizes=None, dtype='float32' )
        new_ds[ variable ].encoding = encoding
            
        # [TODO]: add attrs to the filename
        # - proj4string, metadata, etc...
        new_ds.attrs.update( proj4string=rasterio.open(files[0]).crs.to_string() )
        
        # dump to disk
        new_ds.to_netcdf( out_fn )

