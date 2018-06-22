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

def list_files( path ):
    import glob

    files = glob.glob( os.path.join( path, '*.tif' ) )

    # break up filename attrs
    break_names = [ os.path.basename(fn).split('.')[0].split('_') for fn in files ]
    colnames = ['variable', 'metric', 'units', 'group', 'model', 'scenario', 'month', 'year']

    # make a df and sort chronologically
    df = pd.DataFrame(break_names, columns=colnames )
    df['fn'] = files
    df = df.sort_values(['year', 'month']).reset_index()

    return df.fn.tolist()

def make_nc( path, out_fn, variable ):
    # list and stack em...
    files = list_files( path )
    
    pool = mp.Pool( 32 )
    arr = np.dstack( pool.map( open_raster, files ) )
    pool.close()
    pool.join()

    # get the coordinates as a meshgrid
    x,y = coordinates( fn=files[0] )
    begin = files[0].split( '.' )[0].split('_')[-1]
    end = str(int(files[-1].split( '.' )[0].split('_')[-1]) + 1)
    time = pd.date_range( begin, end, freq='M' )

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
    return out_fn


if __name__ == '__main__':
    import os, glob, rasterio, itertools
    import numpy as np
    import xarray as xr
    import pandas as pd
    import multiprocessing as mp
    import argparse

    # parse some args
    parser = argparse.ArgumentParser( description='stack the hourly outputs from raw WRF outputs to NetCDF files of hourlies broken up by year.' )
    parser.add_argument( "-b", "--base_path", action='store', dest='base_dir', type=str, help="input hourly directory with annual sub-dirs containing hourly WRF NetCDF outputs" )
    parser.add_argument( "-o", "--output_path", action='store', dest='output_dir', type=str, help="output hourly directory with annual sub-dirs containing hourly WRF NetCDF outputs" )
    parser.add_argument( "-m", "--model", action='store', dest='model', type=str, help="model name to process" )
    parser.add_argument( "-s", "--scenario", action='store', dest='scenario', type=str, help="scenario name to process" )
    parser.add_argument( "-v", "--variable", action='store', dest='variable', type=str, help="variable name to process" )
    
    # parse the args and unpack
    args = parser.parse_args()
    base_path = args.base_path
    output_path = args.output_path
    model = args.model
    scenario = args.scenario
    variable = args.variable

    # # # test
    # base_path = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled'
    # output_path = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled_netcdf'
    # model = 'GFDL-CM3'
    # scenario = 'historical'
    # variable = 'tas'
    # # # # # 

    cur_path = os.path.join( base_path, model, scenario, variable )
    if not os.path.exists( cur_path ):
        raise AttributeError( 'check base_path, model, scenario, variable strings for errors, \
                                make sure path exists' )
    try:
        if not os.path.exists( output_path ):
            os.makedirs( output_path )
    except:
        pass

    print( model, scenario )
    # list em
    cur_path = os.path.join( base_path, model, scenario, variable )
    files = glob.glob( os.path.join( cur_path, '*.tif' ) )
    out_fn = os.path.join(output_path,model,scenario,variable,'{}_{}_{}.nc'.format(variable, model,scenario) )
    try:
        dirname = os.path.dirname( out_fn )
        if not os.path.exists( dirname ):
            os.makedirs( dirname )
    except:
        pass

    make_nc( cur_path, out_fn, variable )
