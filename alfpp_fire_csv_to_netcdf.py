# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Preliminary method to convert the ALFRESCO output CSV files to NetCDF objects
# Author: Michael Lindgren (malindgren@alaska.edu) 
#         Geodata Scientist -- Scenarios Network for Alaska + Arctic Planning
# 
# LICENSE: MIT
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class MakeNetCDF( object ):
    def __init__( self, base_path, wildcards, domain_names, variables, *args, **kwargs):
        '''
        Make a NetCDF4 file from the ALFRESCO Fire Model Post-Processes Outputs from 
        `alfresco_postprocessing` csv files.

        ARGUMENTS:
        ---
        base_path = [str] path to the output ALFRESCO PostProcessing folder storing the outputs
        wildcards = [dict] of {variable_name:wildcard}
        domain_names = [list] str list of the sub-domain names *this ensures 1-to-1 matching of values to domain 
        variables = [dict] of {variable_name:dtype} for updating variable encoding for compression

        '''
        self.base_path = base_path
        self.wildcards = wildcards
        self.domain_names = domain_names
        self.variables = variables
        self.years = None
        self.reps = None
        self.names = None
        self.make_dataset()

    def _stacker(self, variable, wildcard):
        ''' names are passed to make sure that we get the right order in all steps'''
        files = glob.glob(os.path.join(os.path.join(self.base_path,variable), wildcard))
        # sort 'em so we are SURE we are getting the right subdomains
        files = [ next(filter(lambda x: dn in x, files)) for dn in self.domain_names]
        frames = OrderedDict([(os.path.basename(fn).split('_')[2],pd.read_csv(fn, index_col=0, parse_dates=True)) for fn in files])
        tmp = frames[list(frames.keys())[0]].copy() # grab the first name to set all the labels the same way.
        # sort the columns
        cols = self.column_sorter(tmp.columns)
        frames = {k:frames[k][cols] for k in frames}
        return np.rollaxis(np.dstack([ frames[n] for n in self.domain_names ]), -1)
    @staticmethod
    def column_sorter(cols):
        colsort = sorted([int(col.split('_')[-1]) for col in cols])
        return [ 'rep_{}'.format(col) for col in colsort ]
    @staticmethod
    def update_encoding_inplace(ds,variable,dtype):
        encoding = ds[variable].encoding.copy()
        encoding.update({ 'zlib':True, 'comp':5, 'contiguous':False, 'dtype':dtype })
        ds[variable].encoding = encoding
        return None
    def make_dataset( self ):
        # stack up the variables in an xarray ready-format
        data = {x:(['name', 'year', 'replicate'], self._stacker(variable=x, wildcard=self.wildcards[x])) for x in self.wildcards }
        
        # we can do all of this with these variables since they have the same dimensionality and the same labels
        # so just grab one and pull the labels
        tmp_fn = glob.glob([os.path.join(self.base_path,x,self.wildcards[x]) for x in self.wildcards][0])[0] # hacky grab single file
        tmp = pd.read_csv( tmp_fn, index_col=0, parse_dates=True )
        # get/modify the labels to make them easier to query
        self.years = tmp.index.map(lambda x: x.strftime('%Y')).astype(int)
        self.reps = tmp.columns.map(lambda x: int(x.split('_')[1])).astype(int)

        # make an xarray Dataset with the stacked csv's
        self.ds = xr.Dataset( data_vars=data,
                         coords={'year': ('year', self.years),
                                'replicate': ('replicate', self.reps),
                                'name':self.domain_names } )

        # variable encoding
        _ = [self.update_encoding_inplace(self.ds,v,self.variables[v]) for v in self.variables]
       

if __name__ == '__main__':
    import os, glob
    import rasterio
    import xarray as xr
    import pandas as pd
    import numpy as np
    from collections import OrderedDict

    # setup variables
    base_path = '/workspace/Shared/Tech_Projects/ALF_JFSP/project_data/ALFRESCO_PostProcessing/FireManagementZones/gcm_tx1/fmo99s95i_rcp85_IPSL-CM5A-LR'
    wildcards = OrderedDict([('total_area_burned','*alfresco_totalareaburned*.csv'), 
                ('avg_fire_size','*alfresco_avgfiresize*.csv'),
                ('number_of_fires','*alfresco_numberoffires*.csv')])
    variables = OrderedDict([('total_area_burned', 'float32'),
                ('avg_fire_size', 'float32'),
                ('number_of_fires', 'int16')])
    domain_names = ['GalenaZone', 'InteriorBoreal', 'TokArea', 'CopperRiverArea', 
                    'DeltaArea', 'KenaiKodiakArea', 'UpperYukonZone', 'ChugachNationalForest', 
                    'SouthwestArea', 'SouthcentralBoreal', 'MatSuArea', 'TananaZone', 'FairbanksArea', 'MilitaryZone']

    # make the dataset
    ds = MakeNetCDF( base_path, wildcards, domain_names, variables ).ds

    # select a single year and rep number
    df = ds.sel(year=2019, replicate=0).to_dataframe()

    # or you can use standard slicing syntax to return ranges of values in one or more of the selection variables
    df_multiindex = ds.sel(year=slice(2010,2079), replicate=0, name='FairbanksArea').to_dataframe() 

    # or subset some stuff and melt the dataframe to a 'long-form' style
    df_sub = ds.sel(year=slice(2010,2079), replicate=0).to_dataframe()
    melted = df_sub.reset_index().melt(id_vars=['replicate','name','year'])

    # and now lets dump it to disk
    out_fn = '/workspace/Shared/Tech_Projects/ALF_JFSP/project_data/test_alfpp_netcdf/alfpp_fire_gcm_tx1_fmo99s95i_rcp85_IPSL-CM5A-LR_FireManagementZones.nc'
    ds.to_netcdf( out_fn, format='NETCDF4' )
