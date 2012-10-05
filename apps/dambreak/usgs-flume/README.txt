This application directory is for a dambreak problem using the shallow water equations over arbitrary topography, specified in a DEM. For simplicity the usgs debris flow flume is used for the topography. For general dambreak problems, supply topography and initialization files. See setrun.py.

Pre-run set-up: to make 'artificial' DEM's of topography and initialization files:

>> python maketopo.py

Note you must have python set-up, and pyclaw on your python path.
See CLAW/setenv.py  or Clawpack documentation for more info.

Note: All parameters regarding setting-up a run are in setrun.py. See file and documentation.

Running a simulation: (this will run setrun.py, set-up all input files, make the executable and run it), type the following:

>> make .output

To simply make data files:

>> make .data

To simply make an executable:

>> make .exe.

See Clawpack documentation for more info on using make.

To run a more general dambreak problem, it probably makes sense to study setrun.py. This python routine controls all set-up for a simulation. Modify according to the specific application. In general problems, it is not necessary to modify anything else. Python scripts are run using make (see above), rather than running them directly.

For plotting:

there is limited support for plotting. Matlab can be used. CLAW/matlabgeo and CLAW/matlab must be in your matlab path. Make sure CLAW/matlabgeo is higher than CLAW/matlab, as some routines have the same name...but matlabgeo is specific to geoclaw output.

To plot, move all files in matlabplotting into _output/. Modify as needed. *_gca.m files provide different views of the flume. These are selected in afterframe.m.

From _output/ run:

MATLABPROMPT>> plotclaw2

select 'yes' for defaults.

