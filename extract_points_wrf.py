# # # #
# Description: an example of how to extract point locations from a wrf-ak-ar5 S3 bucket dataset
# Author: Michael Lindgren (malindgren@alaska.edu)
# License: MIT
#
# REQUIRES Third Party Packages: rasterio, xarray, numpy, pandas, shapely, geopandas 
#    
# # # # 

def affine_from_wrfds( fn ):
    ''' 
    make an affine transform from a downloaded wrf file 
    
    ARGUMENTS:
    ---
    fn = [str] path to the downloaded wrf NetCDF file

    RETURNS:
    ---
    affine transform for the fn passed to the function

    '''
    ds = xr.open_dataset( fn )
    res = 20000
    x0,y0 = np.array( ds.xc.min()-(res/2.)), np.array(ds.yc.max()+(res/2.) )
    ds.close()
    ds = None
    return rasterio.transform.from_origin( x0, y0, res, res )

if __name__ == '__main__':
    import os, subprocess
    import rasterio
    import xarray as xr
    import numpy as np
    import pandas as pd
    from shapely.geometry import Point
    import geopandas as gpd

    # global setup arguments
    variable = 't2'

    path_to_workingdir = './extractions'
    os.chdir( path_to_workingdir )
    
    wrf_dir = os.path.join('.','data')
    if not os.path.exists(wrf_dir):
        _ = os.makedirs(wrf_dir)
    
    os.chdir( './data' )
    download_url = 'http://wrf-ak-ar5.s3.amazonaws.com/hourly/GFDL-CM3/historical/t2/t2_hourly_wrf_GFDL-CM3_historical_1971.nc'
    _ = subprocess.call(['wget', download_url])

    # open the NetCDF dataset using xarray
    filename = os.path.join(path_to_workingdir, 'data', os.path.basename(download_url))
    ds = xr.open_dataset( filename )

    # get an affine transform to make the point lookups faster
    a = affine_from_wrfds( filename )

    # point locations we are going to extract from the NetCDF file
    # these locations are in WGS1984 EPSG:4326
    location = {
            'Fairbanks' : ( -147.716, 64.8378 ),
            'Greely' : ( -145.6076, 63.8858 ),
            'Whitehorse' : ( -135.074, 60.727 ),
            'Coldfoot' : ( -150.1772 , 67.2524 )
            }

    # reproject the points to the wrf-polar-stereo using geopandas
    location = { i:Point(j) for i,j in location.items() }
    df = pd.Series( location ).to_frame( 'geometry' )
    wrf_crs = ds.proj_parameters
    pts_proj = gpd.GeoDataFrame(df, crs={'init':'epsg:4326'}).to_crs( wrf_crs )

    # loop through the locations for extraction
    extracted = {}
    for k, pt in pts_proj.geometry.to_dict().items():      
        # get row/col from x/y using affine
        col, row = ~a * (pt.x, pt.y)
        col, row = [ int(i) for i in [col, row] ]

        # extract
        extracted[ k ] = ds[ variable ][:,row,col].values
        
    # make a dataframe with the extracted outputs
    extracted_df = pd.DataFrame( extracted, index=ds.time.to_index() )

    # write the output extracted values to csv file
    output_path = os.path.join(path_to_workingdir, 'outputs' )
    if not os.path.exists( output_path ):
        _ = os.makedirs( output_path )
    
    extracted_df.to_csv( os.path.join( output_path, 'extracted.csv' ) )




    