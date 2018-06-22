# wrap wrf variable re-stacker for running on slurm nodes
def run( fn, command ):
    import os, subprocess
    ncpus = 32 # take full nodes
    head = '#!/bin/sh\n' + \
            '#SBATCH --ntasks={}\n'.format(ncpus) + \
            '#SBATCH --nodes=1\n' + \
            '#SBATCH --ntasks-per-node={}\n'.format(ncpus) + \
            '#SBATCH --account=snap\n' + \
            '#SBATCH --mail-type=FAIL\n' + \
            '#SBATCH --mail-user=malindgren@alaska.edu\n' + \
            '#SBATCH -p main\n'
    
    with open( fn, 'w' ) as f:
        f.write( head + '\n' + command + '\n' )
    
    # change dir to where you want the log file dumped
    slurm_path, basename = os.path.split( fn )
    os.chdir( slurm_path )
    return subprocess.call([ 'sbatch', fn ])

if __name__ == '__main__':
    import subprocess, os

    # base directory
    base_path = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled'
    output_path = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled_netcdf'
    models = ['5ModelAvg','GFDL-CM3','GISS-E2-R','IPSL-CM5A-LR','MRI-CGCM3','NCAR-CCSM4']
    # models = ['ts40']
    scenarios = [ 'historical', 'rcp45', 'rcp60', 'rcp85' ]
    variables = [ 'clt','hur','pr','rsds','tas','tasmax','tasmin','vap' ]
    script_path = '/workspace/UA/malindgren/repos/etc/snap_monthly_gtiffs_to_netcdf.py'

    slurm_dir = '/workspace/Shared/Tech_Projects/DeltaDownscaling/project_data/downscaled_netcdf/slurm'
    if not os.path.exists( slurm_dir ):
        os.makedirs( slurm_dir )
    os.chdir( slurm_dir )

    for model,scenario,variable in itertools.product(models, scenarios, variables):
        command = ' '.join([ 'python', script_path, '-b', base_path, '-o', output_path, '-m', model, '-s', scenario, '-v', variable ])
        fn = os.path.join( slurm_dir, '{}_stack_month_snap_to_nc.slurm'.format(variable) )
        run( fn, command )





