# ----------------------------------------------
# @author:  Brian Kyanjo
# @contact: briankyanjo@u.boisestate.edu
# @date:    2022-10-16
# @version: 1.0
# ------------------------------------------------

import os
import sys
from pyclaw import data
import numpy as np
from pdb import *

import tools

#===============================================================================
# Importing scripts dictionary
#===============================================================================
sys.path.append('scripts')
# import geoflood # -- importing geoflood.py

#===============================================================================
# scratch directory
#===============================================================================
scratch_dir = os.path.join('../scratch')

#===============================================================================
# User specified parameters
#===============================================================================
#------------------ Time stepping------------------------------------------------
initial_dt = 1  # Initial time step
fixed_dt = False  # Take constant time step

# -------------------- Output files -------------------------------------------------
outstyle = 1

if outstyle == 1:
    # Total number of frames will be frames_per_minute*60*n_hours

    n_hours = 1.2              # Total number of hours in simulation     
    

    frames_per_minute = 60/25   # (1 frame every 25 mins)

if outstyle == 2:
    output_times = [1,2,3]    # Specify exact times to output files

if outstyle == 3:
    step_interval = 10   # Create output file every 10 steps
    total_steps = 1000   # ... for a total of 500 steps (so 50 output files total)

#-------------------  Computational coarse grid ---------------------------------------
mx = 32
my = 32

minlevel = 1
maxlevel = 3 #resolution based on levels 
ratios_x = [4]*(maxlevel-1)
ratios_y = [4]*(maxlevel-1)
ratios_t = [4]*(maxlevel-1)

#-------------------manning coefficient -----------------------------------------------
manning_coefficient = 0.03333

# --------------------- Topography file -----------------------------------------------
topofile = 'scratch/Malpasset/malpasset_domaingrid_20m_nolc.topotype2'
topofile_int = 'scratch/Malpasset/malpasset_resevoir_5m_nolc.topotype2'

# --------------------- Police, transformer and guage data -----------------------------------------------
malpasset_loc = "./malpasset_locs.txt"

#------------------------------
def setrun(claw_pkg='geoclaw'):
#------------------------------

    """
    Define the parameters used for running Clawpack.

    INPUT:
        claw_pkg expected to be "geoclaw" for this setrun.

    OUTPUT:
        rundata - object of class ClawRunData

    """
    #assert claw_pkg.lower() == 'geoclaw',  "Expected claw_pkg = 'geoclaw'"
    ndim = 2
    rundata = data.ClawRunData(claw_pkg, ndim)

    #------------------------------------------------------------------
    # GeoClaw specific parameters:
    #------------------------------------------------------------------

    rundata = setgeo(rundata)   # Defined below


    #------------------------------------------------------------------
    # Standard Clawpack parameters to be written to claw.data:
    #   (or to amr2ez.data for AMR)
    #------------------------------------------------------------------

    clawdata = rundata.clawdata  # initialized when rundata instantiated


    # Set single grid parameters first.
    # See below for AMR parameters.


    # ---------------
    # Spatial domain:
    # ---------------

    # Number of space dimensions:
    clawdata.ndim = ndim

    m_topo,n_topo,xllcorner,yllcorner,cellsize = tools.read_topo_data(topofile)

    # Derived info from the topo map
    mx_topo = m_topo - 1
    my_topo = n_topo - 1
    xurcorner = xllcorner + cellsize*mx_topo
    yurcorner = yllcorner + cellsize*my_topo

    ll_topo = np.array([xllcorner, yllcorner])
    ur_topo = np.array([xurcorner, yurcorner])

    # ll_topo = np.array([957738.41,  1844520.8])
    # ur_topo = np.array([957987.1, 1844566.5])

    
    print("")
    print("Topo domain for %s:" % topofile)
    print("%-12s (%14.8f, %12.8f)" % ("Lower left",ll_topo[0],ll_topo[1]))
    print("%-12s (%14.8f, %12.8f)" % ("Upper right",ur_topo[0],ur_topo[1]))
    print("")

    # dims_topo = ur_topo - ll_topo

    dim_topo = ur_topo - ll_topo
    mdpt_topo = ll_topo + 0.5*dim_topo

    dim_comp = 0.975*dim_topo   # Shrink domain inside of given bathymetry.

    clawdata.xlower = mdpt_topo[0] - dim_comp[0]/2.0
    clawdata.xupper = mdpt_topo[0] + dim_comp[0]/2.0

    clawdata.ylower = mdpt_topo[1] - dim_comp[1]/2.0
    clawdata.yupper = mdpt_topo[1] + dim_comp[1]/2.0

     # Try to match aspect ratio of topo map
    # clawdata.lower = np.array([6.756660, 6.759780])
    # clawdata.upper = np.array([43.512128, 43.512880])
    clawdata.mx = mx
    clawdata.my = my

    print("")
    print("Computational domain")
    print("%-12s (%14.8f, %12.8f)" % ("Lower left",clawdata.xlower,clawdata.ylower))
    print("%-12s (%14.8f, %12.8f)" % ("Upper right",clawdata.xupper,clawdata.yupper))
    print("")

    print("Approximate aspect ratio : {0:16.8f}".format(float(clawdata.mx)/clawdata.my))
    # print("Actual      aspect ratio : {0:16.8f}".format(dims_topo[0]/dims_topo[1]))

    # print "[{0:20.12f},{1:20.12f}]".format(*clawdata.lower)
    # print "[{0:20.12f},{1:20.12f}]".format(*clawdata.upper)

    dims_computed = np.array([clawdata.xupper-clawdata.xlower, clawdata.yupper-clawdata.ylower])
    print("Computed aspect ratio    : {0:20.12f}".format(dims_computed[0]/dims_computed[1]))

    print("")
    print("Details in km : ")    

    lon = np.array([clawdata.xlower,clawdata.xupper])
    lat = np.array([clawdata.ylower,clawdata.yupper])
    d = tools.compute_distances(lon,lat)
   
    # ---------------
    # Size of system:
    # ---------------

    # Number of equations in the system:
    clawdata.meqn = 3

    # Number of auxiliary variables in the aux array (initialized in setaux)
    clawdata.maux = 3

    # Index of aux array corresponding to capacity function, if there is one:
    clawdata.mcapa = 0 # flag set to 0 if coordinate system = 1 otherwise 2

    # -------------
    # Initial time:
    # -------------

    clawdata.t0 = 0.0


    # Restart from checkpoint file of a previous run?
    # Note: If restarting, you must also change the Makefile to set:
    #    RESTART = True
    # If restarting, t0 above should be from original run, and the
    # restart_file 'fort.chkNNNNN' specified below should be in
    # the OUTDIR indicated in Makefile.

    # clawdata.restart = False               # True to restart from prior results
    # clawdata.restart_file = 'fort.chk00006'  # File to use for restart data

    # -------------
    # Output times:
    #--------------

    # Specify at what times the results should be written to fort.q files.
    # Note that the time integration stops after the final output time.
    # The solution at initial time t0 is always written in addition.

    clawdata.outstyle = outstyle

    if clawdata.outstyle == 1:
        # Output nout frames at equally spaced times up to tfinal:
        # n_hours = 20.0
        # frames_per_minute = 1/30.0 # Frames every 5 seconds
        clawdata.nout = int(frames_per_minute*60*n_hours)  # Plot every 10 seconds
        clawdata.tfinal = 60*60*n_hours
        # clawdata.output_t0 = True  # output at initial (or restart) time?

    elif clawdata.outstyle == 2:
        # Specify a list of output times.
        clawdata.tout =  [10.0,53.0e3,55.e3]

        clawdata.nout = len(clawdata.tout)

    elif clawdata.outstyle == 3:
        # Output every iout timesteps with a total of ntot time steps:
        iout = 1
        ntot = 3
        clawdata.iout = [iout, ntot]


    clawdata.output_format = 'ascii'      # 'ascii' or 'netcdf'

    clawdata.output_q_components = 'all'   # could be list such as [True,True]
    clawdata.output_aux_components = 'none'  # could be list
    clawdata.output_aux_onlyonce = True    # output aux arrays only at t0



    # ---------------------------------------------------
    # Verbosity of messages to screen during integration:
    # ---------------------------------------------------

    # The current t, dt, and cfl will be printed every time step
    # at AMR levels <= verbosity.  Set verbosity = 0 for no printing.
    #   (E.g. verbosity == 2 means print only on levels 1 and 2.)
    clawdata.verbosity = 1



    # --------------
    # Time stepping:
    # --------------

    # if dt_variable==1: variable time steps used based on cfl_desired,
    # if dt_variable==0: fixed time steps dt = dt_initial will always be used.
    clawdata.dt_variable = 1

    # Initial time step for variable dt.
    # If dt_variable==0 then dt=dt_initial for all steps:
    clawdata.dt_initial = initial_dt

    # Max time step to be allowed if variable dt used:
    clawdata.dt_max = 1e+99

    # Desired Courant number if variable dt used, and max to allow without
    # retaking step with a smaller dt:
    clawdata.cfl_desired = 0.75
    clawdata.cfl_max = 0.99

    # Maximum number of time steps to allow between output times:
    clawdata.max_steps = 100000

    # ------------------
    # Method to be used:
    # ------------------

   # Order of accuracy:  1 => Godunov,  2 => Lax-Wendroff plus limiters
    clawdata.order = 2

    # Transverse order for 2d or 3d (not used in 1d):
    clawdata.order_trans = 2

    # Number of waves in the Riemann solution:
    clawdata.mwaves = 3

    # List of limiters to use for each wave family:
    # Required:  len(mthlim) == mwaves
    clawdata.mthlim = [4,4,4]

    # Source terms splitting:
    #   src_split == 0  => no source term (src routine never called)
    #   src_split == 1  => Godunov (1st order) splitting used,
    #   src_split == 2  => Strang (2nd order) splitting used,  not recommended.
    clawdata.src_split = 1


    # --------------------
    # Boundary conditions:
    # --------------------

    # Number of ghost cells (usually 2)
    clawdata.mbc = 2

    # Choice of BCs at xlower and xupper:
    #   0 => user specified (must modify bcN.f to use this option)
    #   1 => extrapolation (non-reflecting outflow)
    #   2 => periodic (must specify this at both boundaries)
    #   3 => solid wall for systems where q(2) is normal velocity

    clawdata.mthbc_xlower = 1
    clawdata.mthbc_xupper = 1

    clawdata.mthbc_ylower = 1
    clawdata.mthbc_yupper = 1


    # ---------------
    # AMR parameters:
    # ---------------


    # max number of refinement levels:
    mxnest = maxlevel

    clawdata.mxnest = -mxnest   # negative ==> anisotropic refinement in x,y,t

    # List of refinement ratios at each level (length at least mxnest-1)
    clawdata.inratx = ratios_x
    clawdata.inraty = ratios_y
    clawdata.inratt = ratios_t

    # Instead of setting inratt ratios, set:
    # geodata.variable_dt_refinement_ratios = True
    # in setgeo.
    # to automatically choose refinement ratios in time based on estimate
    # of maximum wave speed on all grids at each level.


    # Specify type of each aux variable in clawdata.auxtype.
    # This must be a list of length maux, each element of which is one of:
    #   'center',  'capacity', 'xleft', or 'yleft'  (see documentation).

    clawdata.auxtype = ['center','center','yleft']


    clawdata.tol = -1.0     # negative ==> don't use Richardson estimator
    clawdata.tolsp = 0.5    # used in default flag2refine subroutine
                            # (Not used in geoclaw!)

    clawdata.kcheck = 3     # how often to regrid (every kcheck steps)
    clawdata.ibuff  = 3     # width of buffer zone around flagged points
    clawdata.cutoff = 0.7   # efficiency cutoff for grid generator
    clawdata.checkpt_iousr = 10000000
    clawdata.restart = False
    # More AMR parameters can be set -- see the defaults in pyclaw/data.py


    clawdata.fortq = False  # output fort.q* files
    # clawdata.tprint = True  # time step reporting each level
    # clawdata.rprint = True  #  print regridding summary
    # clawdata.uprint = True  #  update/upbnd reporting
    # clawdata.PRINT = True  # grid bisection/clustering report




    return rundata
    # end of function setrun
    # ----------------------

#-------------------
def setgeo(rundata):
#-------------------
    """
    Set GeoClaw specific runtime parameters.
    For documentation see ....
    """

    try:
        geodata = rundata.geodata
    except:
        print("*** Error, this rundata has no geodata attribute")
        raise AttributeError("Missing geodata attribute")

    # == Physics ==
    # == setgeo.data values ==
    R1=6357.e3 #polar radius
    R2=6378.e3 #equatorial radius
    Rearth=.5*(R1+R2)
    geodata.igravity = 1
    geodata.gravity = 9.81
    geodata.icoordsys = 1 #set to 2 for use with lat-lon coordinates on the sphere
    geodata.icoriolis = 0
    geodata.Rearth = Rearth

    # == settsunami.data values ==
    geodata.sealevel = 0.0
    geodata.drytolerance = 1.e-3
    geodata.wavetolerance = 5.e-3 #for use with tsunami modeling. ignored when using flowgrades
    geodata.depthdeep = 1.e2 #for use with tsunami modeling. ignored when using flowgrades
    geodata.maxleveldeep = maxlevel #for use with tsunami modeling. ignored when using flowgrades
    geodata.ifriction = 1 #use friction?
    geodata.coeffmanning = manning_coefficient
    geodata.frictiondepth = 10000.0 #friction only applied with depths less than this

    # == settopo.data values ==
   
    # for topography, append lines of the form
    #    [topotype, minlevel, maxlevel, t1, t2, fname]
    # topo_data.topofiles.append([1, minlevel, maxlevel, 0, 1e10, 'scratch/Malpasset/malpasset_topo.xyz'])
    geodata.topofiles = []

    geodata.topofiles.append([2, minlevel, minlevel, 0, 1e10, 'scratch/Malpasset/malpasset_domaingrid_20m_nolc.topotype2'])
    geodata.topofiles.append([2, minlevel+1, minlevel+1, 0, 1e10, 'scratch/Malpasset/malpasset_resevoir_5m_nolc.topotype2'])
    geodata.topofiles.append([2, minlevel, maxlevel, 0, 1e10, 'scratch/Malpasset/malpasset_grid4_2m_nolc.topotype2'])
    geodata.topofiles.append([2, minlevel, maxlevel, 0, 1e10, 'scratch/Malpasset/malpasset_grid3_2m_nolc.topotype2'])
    geodata.topofiles.append([2, minlevel, maxlevel, 0, 1e10, 'scratch/Malpasset/malpasset_grid2_1m_nolc.topotype2'])
    geodata.topofiles.append([2, minlevel, maxlevel, 0, 1e10, 'scratch/Malpasset/malpasset_damapproach_1m_nolc.topotype2'])

    # == setqinit.data values ==
    geodata.qinitfiles = []

    # for qinit perturbations append lines of the form
    #   [qinitftype,iqinit, minlev, maxlev, fname]
    
    geodata.qinitfiles.append([1,4,minlevel,minlevel,'scratch/Malpasset/init_eta_5m_cadam.xyz'])

    # == setauxinit.data values ==
    # geodata.auxinitfiles = []

    # == setregions.data values ==
    geodata.regions = []
    # to specify regions of refinement append lines of the form
    #  [minlevel,maxlevel,t1,t2,x1,x2,y1,y2]
    #geodata.regions.append([])

    # Region containing initial reservoir
    def get_topo(topofile):
        m_topo,n_topo,xllcorner,yllcorner,cellsize = tools.read_topo_data(topofile)

        # Derived info from the topo map
        mx_topo = m_topo - 1
        my_topo = n_topo - 1
        xurcorner = xllcorner + cellsize*mx_topo
        yurcorner = yllcorner + cellsize*my_topo

        ll_topo = np.array([xllcorner, yllcorner])
        ur_topo = np.array([xurcorner, yurcorner])

        dim_topo = ur_topo - ll_topo
        mdpt_topo = ll_topo + 0.5*dim_topo

        dim_comp = 0.975*dim_topo   # Shrink domain inside of given bathymetry.

        xlower = mdpt_topo[0] - dim_comp[0]/2.0
        xupper = mdpt_topo[0] + dim_comp[0]/2.0

        ylower = mdpt_topo[1] - dim_comp[1]/2.0
        yupper = mdpt_topo[1] + dim_comp[1]/2.0

        return [dim_topo, [xlower, ylower], [xupper, yupper]]

    dims_topo, lower, upper = get_topo(topofile_int)
    geodata.regions.append([maxlevel,maxlevel,0, 1e10, lower[0],upper[0],lower[1],upper[1]])
    print("")
    print("Initial reservoir domain")
    print("%-12s (%14.8f, %12.8f)" % ("Lower left",lower[0],lower[1]))
    print("%-12s (%14.8f, %12.8f)" % ("Upper right",upper[0],upper[1]))
    print("")

    # == setgauges.data values ==
    geodata.gauges = []
    # for gauges append lines of the form  [gaugeno, x, y, t0, tf]
    #geodata.gauges.append([1, -155.056, 19.731, 50.e3, 60e3])
    # Gauges ( append lines of the form  [gaugeno, x, y, t1, t2])
    police, transformers, gauges, all_guages = tools.read_locations_data(malpasset_loc)

    print('\nLocation of Gauges:')
    for i in range(len(all_guages[0])):
        print('\tGauge %s at (%s, %s)' % (all_guages[0][i], all_guages[1][i],all_guages[2][i]))
        geodata.gauges.append([all_guages[0][i], all_guages[1][i],all_guages[2][i], 0., 1e10])


     # == setflowgrades.data values ==
    # geodata.flowgrades = []
    # geodata.flowgrades.append([1.e-3, 2, 1, 3])
    # geodata.flowgrades.append([1.e-4, 1, 1, 3])

    return rundata
    # end of function setgeo
    # ----------------------

if __name__ == '__main__':
    # Set up run-time parameters and write all data files.
    import sys

    if len(sys.argv) == 2:
        rundata = setrun(sys.argv[1])
    else:
        rundata = setrun()

    rundata.write()
