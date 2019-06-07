# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Preliminary method to convert the ALFRESCO output CSV files to NetCDF objects
# Author: Michael Lindgren (malindgren@alaska.edu) 
#         Geodata Scientist -- Scenarios Network for Alaska + Arctic Planning
# 
# LICENSE: MIT
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def run_stacker(base_path, wildcard):
    files = glob.glob(os.path.join(base_path, wildcard))
    frames = {os.path.basename(fn).split('_')[2]:pd.read_csv(fn, index_col=0, parse_dates=True) for fn in files}
    names = list(frames.keys())
    return np.rollaxis(np.dstack([ frames[n] for n in names ]), -1)

def update_encoding_inplace(ds,variable,dtype):
    encoding = ds[variable].encoding.copy()
    encoding.update({ 'zlib':True, 'comp':5, 'contiguous':False, 'dtype':dtype })
    ds[variable].encoding = encoding
    return None

if __name__ == '__main__':
    import os, glob
    import rasterio
    import xarray as xr
    import pandas as pd
    import numpy as np

    # setup variables
    base_path = '/workspace/Shared/Tech_Projects/ALF_JFSP/project_data/ALFRESCO_PostProcessing/FireManagementZones/gcm_tx1/fmo99s95i_rcp85_IPSL-CM5A-LR'
    wildcards = {'total_area_burned':'*alfresco_totalareaburned*.csv', 
                'avg_fire_size':'*alfresco_avgfiresize*.csv',
                'number_of_fires':'*alfresco_numberoffires*.csv'}
    variables = {'total_area_burned':'float32', 
                'avg_fire_size':'float32',
                'number_of_fires':'int16'}
    
    # stack up the variables in an xarray ready-format
    data = {x:(['name', 'year', 'replicate'], run_stacker(os.path.join(base_path,x),wildcards[x])) for x in wildcards }
    
    # we can do all of this with these variables since they have the same dimensionality and the same labels
    rlabels = frames[names[0]].index
    clabels = frames[names[0]].columns

    # modify the labels to make them easier to query
    years = rlabels.map(lambda x: x.strftime('%Y')).astype(int)
    reps = clabels.map(lambda x: int(x.split('_')[1])).astype(int)

    # make an xarray Dataset with the stacked csv's
    ds = xr.Dataset( data_vars=data,
                     coords={'year': ('year', years),
                            'replicate': ('replicate', reps),
                            'name':names } )

    # select a single year and rep number
    df = ds.sel(year=2019, replicate=0).to_dataframe()

    # or you can use standard slicing syntax to return ranges of values in one or more of the selection variables
    df_multiindex = ds.sel(year=slice(2019,2030), replicate=0).to_dataframe()

    # now lets update the encoding on the variables to see if we can gain some compression
    _ = [update_encoding_inplace(ds,v,variables[v]) for v in variables]

    # and now lets dump it to disk
    out_fn = '/workspace/Shared/Tech_Projects/ALF_JFSP/project_data/test_alfpp_netcdf/alfpp_fire_gcm_tx1_fmo99s95i_rcp85_IPSL-CM5A-LR_FireManagementZones.nc'
    ds.to_netcdf( out_fn, format='NETCDF4' )
