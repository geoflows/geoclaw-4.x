---
title: geoclaw-4.x
subtitle: software for shallow water flow (shallow water equations) for tsunamis and overland flow.
description: geoclaw-4.x is based on early versions of TsunamiClaw based on clawpack-4.x (clawpack.org). See also clawpack.org for more recent versions of GeoClaw and part of the current development clawpack versions 5.x.
---

---

# Overview

GeoClaw (geoclaw-4.x) is based on clawpack-4.x software. This version is developed from the original TsunamiClaw code, but includes additional functionality, particularly for overland flow. Newer versions of GeoClaw are based on the current versions of clawpack, and are available with clawpack 5.x codes. See www.clawpack.org. 

(The older v4.x version of Clawpack is available at [github.com/clawpack/clawpack-4.x](https://github.com/clawpack/clawpack4.x). See [clawpack.org](http://www.clawpack.org) for more information.) 

The basics of running it are below. See also the [geoflows/dclaw-apps](https://github.com/geoflows/dclaw-apps) on github for examples.


# Use

To use GeoClaw 4.x as is, it is assumed that you have a unix terminal of some kind (*eg.,* linux or Mac OS...for MS Windows you are on your own, but options exist for terminal emulators). 

## Source code

The source code and latest git repository are available on github:

* [github.com/geoflows/geoclaw-4.x](https://github.com/geoflows/geoclaw-4.x).

A repository for applications for GeoClaw 4.x and D-Claw (in progress) is also available:

* [github.com/geoflows/dclaw-apps](https://github.com/geoflows/dclaw-apps).

If you want just the source code without using git, github provides a zipped directory. Otherwise, you can clone either of the repositories with git clone as usual:

```
git clone https://github.com/geoflows/geoclaw-4.x.git
```
and
```
git clone https://github.com/geoflows/dclaw-apps.git
```
 

## Installation

"Installation" of GeoClaw 4.x is essentially just setting some environment variables. Compiling and running GeoClaw 4.x can then be done using make, with a Makefile in an application directory.  

#### environment variables

The environment variable $CLAW should be set to point to the parent directory of the source code. For bash shells:
```
export CLAW=/path/to/geoclaw-4.x
```

TIP: if you are using multiple versions of Clawpack (*eg.,* Clawpack 5.x or GeoClaw and D-Claw), it is advisable to stay mindful of how $CLAW is set, particularly if you are developing/testing code. It is easy to inadvertently compile the wrong code, or fail to incorporate code-changes if $CLAW is set incorrectly. Packages such as the [environment modules](http://modules.sourceforge.net/) package, which can dynamically set or change your environment under a given shell to ensure that you have a compatible set of paths/versions of software (*eg.*, $PATH, $CLAW, $PYTHONPATH, $MATLABPATH), are very useful.

(Alternatively, one could modify Makefiles if you want to use an environment variable other than $CLAW, such as $GEOCLAW. However, this can add complications to your path hierarchy for python and matlab when switching between different $CLAWs, as there are modified routines with the same file name...and so it is not recommended without something like environmental modules.)   

#### python
In order to use the python set-up scripts that are included, you should include $CLAW/python/ in your $PYTHONPATH:
```
export PYTHONPATH=$CLAW/python:$PYTHONPATH
```
You can also then import some auxiliary tools from the GeoClaw python folder if you find them useful:  
```
python> import geoclaw
python> import geoclaw.topotools as gt 
```
See the comments in these modules for more information.

NOTE: The current version of GeoClaw 4.x is compatible with python v2.x. If you prefer python version v3.x, see below about developing and contributing.    

#### matlab
If you are going to use matlab plotting, your $MATLABPATH should include $CLAW/matlabgeo, above but in addition to $CLAW/matlab:
```
export MATLABPATH=$CLAW/matlabgeo:$CLAW/matlab:$MATLABPATH
```

## Running a GeoClaw 4.x simulation

Running applications is very similar to running applications in Clawpack v5.x. See the documentation at [clawpack.org](http://www.clawpack.org). See also example applications that include necessary files in the application repository, [github/geoflows/dlcaw-apps](https://github.com/geoflows/dclaw-apps).

The GeoClaw executable is made entirely from Fortran source code. However, python is used to set-up and initialize a given run, and optionally plot the results. Therefore, ordinary use of GeoClaw requires interaction with python scripts and the make program. Modifying Fortran source code is only necessary if you are developing new features or debugging.

#### directory and file structure

In summary, a working application directory (it is recommended that this reside away from your source code) for a single simulation should contain:
* a Makefile
* python initialization scripts (setrun.py)
* optional plotting routines (python or matlab)
* optional pre-processing routines for topography or other data requirements

Setting up a given simulation essentially amounts to modifying the routine setrun.py, to set runtime parameters, initial conditions, and required input data (*eg.,* topography DEMs). Plotting can be done with python or matlab scripts, which are included with GeoClaw and application examples (*see* *eg.,* [geoclaw/dclaw-apps](https://github.com/geoclaw/dclaw-apps) on github). See more info on plotting below, or in example applications.

#### make 


```
pwd

/path/to/myapplication/
```

To recompile all of the Fortran source code from scratch and create a new executable ("xgeoclaw"), issue:

```
make new
```
 
The following make commands will take into account dependency changes to determine the sequence of prerequisite steps that need to be taken. To make or retain an up-to-date executable, issue: 
```
make .exe
```

To run the executable and produce output (the output files will be placed in a subdirectory indicated in the Makefile), issue:
```
make .output
```

To produce plots using python and the setplot.py routine in your application directory, issue: 
```
make .plots
```

Note that each one of the above steps depends on the previous steps if source code or parameters have changed. So, for instance, "make .plots" will recompile source code, rerun the executable to produce new output, and finally produce new plots if the source code has changed. If only setrun.py has been modified, it will re-run the existing executable to produce new output. If nothing has changed, make will indicate that nothing needs to be done.

**WARNING: if the commands `make .output` or `make .plots` create a new run, previously made output files in the `_output` directory will be deleted. If you have changed source code or runtime parameters, but wish to keep your old output for comparison or debugging, take necessary action to save your old files. The Makefile can also be modified to specify your output directory name.** 

To produce plots with python without checking dependencies, without the risk of deleting wanted output files, you can issue:
```
make plots
```
 (without the ".").

## Plotting results
#### matlab

Matlab can be used to plot GeoClaw output. From the output directory, use
```
matlab> plotclaw2
```
then follow the interactive menu to produce plots for each frame.

TIP: For a given application, it is useful to relocate some of the m-files (*eg.,* afterframe.m, setplot2.m, setprob.m, beforeframe.m etc.) included with GeoClaw to your local working application directory, where you can modify them to suit you present purposes without modifying your source files (note that files in $CLAW/matlabgeo should take precedent over files of the same name in $CLAW/matlab. Unifying these directories is planned in the future, but they currently coexist so that the source code can be used to run Geoclaw v4.x applications...more about that in the future). 

TIP: Note that output and these locally modified .m-files (in your application directory) must both be located by matlab, but they are not usually in the same directory. For instance, if the output sub-directory is the current directory where matlab is running, *ie.,*
```
matlab> pwd
/path/to/myapplication/_output
```
then you can issue,
```
matlab> addpath ../
```
to get the local .m-files in the output's parent directory, myapplication/, to the top of your path (*ie.* Matlab will add the absolute path for ../ to the top of your path for the current session).

NOTE: you could alternatively place your local m-files in the output directory...but this is not recommended if you want your local m-files to be part of a repository, as the output directory is best ignored by git, as it is with the applications in the [dclaw-apps](https://github.com/geoflows/dclaw-apps).

More information on plotting can be found in the [dclaw-apps](https://github.com/geoflows/dclaw-apps) repository.


#### python

Python can alternatively be used to produce mapview 2D or 1D cross-sectional plots, as describe above, with:
```
make .plots
```
or
```
make plots
```
Make uses setplot.py and matplotlib.  Modify the routine setplot.py to your needs. 

See [clawpack.org](http://www.clawpack.org), [github/clawpack/visclaw](https://gihub.com/clawpack/visclaw) and [github/geoflows/dclaw-apps](https://github.com/geoflows/dclaw-apps) for more information.


## Development

* If you would like to make contributions to GeoClaw 4.x, D-Claw or dclaw-apps, please follow the development workflow used for Clawpack, described at [www.clawpack.org/developers](http://www.clawpack.org/developers.html). In summary, please fork the repositories to your own github account, and issue pull requests on a feature branch to github/geoflows, *eg,*:

```
git clone https://github.com/geoflows/geoclaw-4.x.git 
cd geoclaw-4.x
git remote add username https://github.com/username/geoclaw-4.x.git
```
or if you have ssh keys and want to avoid typing your password when you push to github:

```
git remote add username git@github.com:username/geoclaw-4.x.git
```
These settings can be modified in your local working repository at anytime with `git remote set-url`.

* Develop in a branch other than master:
```
git checkout -b my_branch
```
And then push to your repository on github:
```
git push username my_branch
```
* Issue pull requests from your branch and repository on github.com (username/geoclaw-4.x) to contribute features or fixes to the GeoClaw4.x master branch at geoflows/geoclaw-4.x. 

* Update your master branches from geoflows/geoclaw-4.x:
```
git pull origin master
```
and then 
```
git push username master
```
to update your git remote. It is recommended that you do not commit to your own master branches, so that your master branches are easily updated from the geoflows repository.

If you prefer, rename origin to something easy to remember ("geoflows" or "upstream" or similar):
```
git remote rename origin geoflows
```

## License

geoclaw-4.x inherits the Clawpack licenses and user agreeements. 