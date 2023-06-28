#!/usr/bin/env python
# encoding: utf-8
"""
file: topotools.py

   Provides several useful functions
   for manipulating topography data.

Contains:
   get_topo:     downloads topo file from GeoClaw repository on web.
   topo1writer:  create files of topotype1 from synthetic topo function.
   topo2writer:  create files of topotype2 from synthetic topo function.
   gcdist:       computes great circle distance between points on sphere.
   dx_from_gcdist:  inverts gcdist function at a give latitude.

   scatter2gridded
   topoheaderread
   topoheaderwrite
   topofile2griddata
   griddata2topofile
   griddatasubset
   topofilesubset
   topofilesubsample
   topofilefindz
   converttopotype
   removenodata_value
   changenodata_value
   burnin_nodata
   swapheader

Authors: Dave George and Randy LeVeque

"""

import os
import string

import numpy as np

import dclaw.fixdata as fixdata
import dclaw.iotools as iotools

Rearth = 6367.5e3  # average of polar and equatorial radii


# ==========================================================================


def get_topo(topo_fname, remote_directory, force=None):
    """
    Download a topo file from the web, provided the file does not
    already exist locally.

    remote_directory should be a URL.  For GeoClaw data it may be a
    subdirectory of  http://kingkong.amath.washington.edu/topo/
    See that website for a list of archived topo datasets.

    If force==False then prompt the user to make sure it's ok to download,
    with option to first get small file of metadata.

    If force==None then check for environment variable CLAW_TOPO_DOWNLOAD
    and if this exists use its value.  This is useful for the script
    python/run_examples.py that runs all examples so it won't stop to prompt.
    """
    import urllib.error
    import urllib.parse
    import urllib.request

    if force is None:
        CTD = os.environ.get("CLAW_TOPO_DOWNLOAD", None)
        force = CTD in [True, "True"]
    print(("force = ", force))

    if os.path.exists(topo_fname):
        print(("*** Not downloading topo file (already exists): %s " % topo_fname))
    else:
        remote_fname = topo_fname
        local_fname = topo_fname
        remote_fname_txt = remote_fname + ".txt"
        local_fname_txt = local_fname + ".txt"

        print(("Require remote file ", remote_fname))
        print(("      from ", remote_directory))
        if not force:
            ans = eval(
                input(
                    "  Ok to download topo file?  \n"
                    + "     Type y[es], n[o] or ? to first retrieve and print metadata  "
                )
            )
            if ans.lower() not in ["y", "yes", "?"]:
                print(("*** Aborting!   Missing: ", local_fname))
                return
            if ans == "?":
                try:
                    print(("Retrieving remote file ", remote_fname_txt))
                    print(("      from ", remote_directory))
                    url = os.path.join(remote_directory, remote_fname_txt)
                    urllib.request.urlretrieve(url, local_fname_txt)
                    os.system("cat %s" % local_fname_txt)
                except:
                    print("*** Error retrieving metadata file!")
                ans = eval(input("  Ok to download topo file?  "))
                if ans.lower() not in ["y", "yes", "?"]:
                    print(("*** Aborting!   Missing: ", local_fname))
                    return

        if not os.path.exists(local_fname_txt):
            try:
                print(("Retrieving metadata file ", remote_fname_txt))
                print(("      from ", remote_directory))
                url = os.path.join(remote_directory, remote_fname_txt)
                urllib.request.urlretrieve(url, local_fname_txt)
            except:
                print("*** Error retrieving metadata file!")

        try:
            print(("Retrieving topo file ", remote_fname))
            print(("      from ", remote_directory))
            url = os.path.join(remote_directory, remote_fname)
            urllib.request.urlretrieve(url, local_fname)
        except:
            print(("*** Error retrieving file!  Missing: ", local_fname))
            raise Exception("Error from urllib.urlretrieve")
        try:
            firstline = open(local_fname, "r").readline()
            if firstline.find("DOC") > -1:
                print(("*** Possible error -- check the file ", local_fname))
            else:
                print(("Saved to ", local_fname))
        except:
            raise Exception("Error opening file %s" % local_fname)


# ==========================================================================
def topo1writer(outfile, topo, xlower, xupper, ylower, yupper, nxpoints, nypoints):
    """
    Function topo1writer will write out the topofiles by evaluating the
    function topo on the grid specified by the other parameters.

    Assumes topo can be called on arrays X,Y produced by np.meshgrid.

    Output file is of "topotype1," which we use to refer to a file with
    (x,y,z) values on each line, progressing from upper left corner across
    rows, then down.
    """

    fout = open(outfile, "w")
    dx = (xupper - xlower) / (nxpoints - 1)
    dy = (yupper - ylower) / (nypoints - 1)

    x = np.linspace(xlower, xupper, nxpoints)
    y = np.linspace(ylower, yupper, nypoints)
    X, Y = np.meshgrid(x, y)
    Z = topo(X, Y).T

    for jj in range(0, nypoints):
        y = yupper - jj * dy
        for i in range(0, nxpoints):
            x = xlower + i * dx
            j = nypoints - 1 - jj
            z = Z[i, j]
            fout.write("%22.15e  %22.15e  %22.15e\n" % (x, y, z))

    fout.close
    print(("Created file ", outfile))


# ==========================================================================
def topo2writer(
    outfile,
    topo,
    xlower,
    xupper,
    ylower,
    yupper,
    nxpoints,
    nypoints,
    nodata_value=-99999,
):
    """
    Function topo2writer will write out the topofiles by evaluating the
    function topo on the grid specified by the other parameters.

    Assumes topo can be called on arrays X,Y produced by np.meshgrid.

    Output file is of "topotype2," which we use to refer to a file with a
    header and one z value of topography per row in the file

    Header is of the form:
    # ---------------------------
    # integer   ncols   (= nxpoints)
    # integer   nrows   (= nypoints)
    # double    xlower
    # double    ylower
    # double    cellsize
    #integer   nodata_value
    # -----------------------------
    """

    # note: for topotype2, dx=dy=cellsize
    dx = (xupper - xlower) / (nxpoints - 1)
    dy = (yupper - ylower) / (nypoints - 1)
    if abs(dx - dy) > 1.0e-8:
        print("*** Error in topo2writer, need dx=dy")
        print(("    dx = %s, dy = %s" % (dx, dy)))
        return
    cellsize = dx

    nrows = nypoints
    ncols = nxpoints
    dx = cellsize
    dy = cellsize

    fout = open(outfile, "w")
    fout.write("%6i                              %s\n" % (ncols, "ncols"))
    fout.write("%6i                              %s\n" % (nrows, "nrows"))
    fout.write("%22.15e              %s\n" % (xlower, "xlower"))
    fout.write("%22.15e              %s\n" % (ylower, "ylower"))
    fout.write("%22.15e              %s\n" % (cellsize, "cellsize"))
    fout.write("%10i                 %s\n" % (nodata_value, "nodata_value"))

    x = np.linspace(xlower, xupper, nxpoints)
    y = np.linspace(ylower, yupper, nypoints)
    X, Y = np.meshgrid(x, y)
    Z = topo(X, Y).T

    for jj in range(0, nrows):
        for i in range(0, ncols):
            j = nypoints - 1 - jj
            fout.write("%22.15e\n" % Z[i, j])

    fout.close
    print(("Created file ", outfile))


# ==========================================================
def gcdist(x1, y1, x2, y2, Rsphere=Rearth, units="degrees"):
    """
    Compute the great circle distance on the earth between points
    (x1,y1) and (x2,y2), where:
    x = longitude, y = latitude
    """
    from numpy import arccos, arcsin, cos, pi, sin, sqrt

    if units == "degrees":
        # convert to radians:
        x1 = x1 * pi / 180.0
        y1 = y1 * pi / 180.0
        x2 = x2 * pi / 180.0
        y2 = y2 * pi / 180.0
    elif units != "radians":
        raise Exception("unrecognized units")

    dx = x1 - x2
    dy = y1 - y2

    # angle subtended by two points, using Haversine formula:
    dsigma = 2.0 * arcsin(
        sqrt(sin(0.5 * dy) ** 2 + cos(y1) * cos(y2) * sin(0.5 * dx) ** 2)
    )

    # alternative formula that may have more rounding error:
    # dsigma2 = arccos(sin(y1)*sin(y2)+ cos(y1)*cos(y2)*cos(dx))
    # print "max diff in dsigma: ", abs(dsigma-dsigma2).max()

    d = Rsphere * dsigma
    return d


# ==========================================================
def dx_from_gcdist(d, x1, y1, y2, Rsphere=Rearth, units="degrees"):
    """
    Invert the gcdist function to find dx given distance d and (x1,y1) and y2.
    The corresponding x2 can be x1+dx or x1-dx.
    May return NaN if no solution.
    """
    from numpy import arccos, cos, pi, sin

    if units == "degrees":
        # convert to radians:
        x1 = x1 * pi / 180.0
        y1 = y1 * pi / 180.0
        y2 = y2 * pi / 180.0
    elif units != "radians":
        raise Exception("unrecognized units")
    dsigma = d / Rsphere
    cos_dsigma = (cos(dsigma) - sin(y1) * sin(y2)) / (cos(y1) * cos(y2))
    dx = arccos(cos_dsigma)
    if units == "degrees":
        dx = dx * 180.0 / pi
    return dx


# ==============================================================================================
def scatter2gridded(
    scatterdatafile=" ", boundarydatafile=" ", headerfile=" ", outputfile=" "
):

    """
    scatter2gridded (scatterdatafile=" ",boundarydatafile=" ", headerfile=" ", outputfile=" "):

    function converts scattered data points (x,y,z) into
    gridded data, with z values given at uniformly spaced points.

    'scatterdatafile' and optional 'boundarydatafile' should each have three columns
     containing x,y,z coordinates respectively of each point.

    'headerfile' specifies the format of the grid parameters for the output data.
     The header should have the following form:

         int ncols
         int nrows
         float xll
         float yll
         float cellsize
         float nodata_value

    see topotools.headerwriter and topotools.headerreader.

    'outputfile' will have the same header followed by the data advancing from northwest
    across eastward then down, one z value per row.
    """
    import pylab

    # Input data==========================:
    # read scattered data
    fin = open(scatterdatafile, "r")
    a = np.fromfile(fin, sep=" ", count=-1, dtype=float)
    fin.close
    # read boundary data ie: points specifying a quadrilateral bounding the scattered data if it is needed
    if boundarydatafile != " ":
        fin = open(boundarydatafile, "r")
        b = np.fromfile(fin, sep=" ", count=-1, dtype=float)
        fin.close
        a = np.hstack((a, b))
    # reshape data into (#pts , 3) array
    pts = len(a) / 3

    a = np.reshape(a, (pts, 3))

    # determine what the output grid will look like from headerfile
    topoheader = topoheaderread(inputfile=headerfile)

    # manipulate data============================:
    # Create the gridded data using pylab "griddata function."
    xgrid = np.arange(
        topoheader["xll"],
        topoheader["xll"] + topoheader["ncols"] * topoheader["cellsize"],
        step=topoheader["cellsize"],
        dtype=float,
    )
    ygrid = np.arange(
        topoheader["yll"],
        topoheader["yll"] + topoheader["nrows"] * topoheader["cellsize"],
        step=topoheader["cellsize"],
        dtype=float,
    )

    X, Y = np.meshgrid(xgrid, ygrid)

    Z = pylab.griddata(a[:, 0], a[:, 1], a[:, 2], X, Y)
    Y = np.flipud(Y)
    Z = np.flipud(Z)
    #    pyplot.contour(X,Y,Z)
    # write the output file =====================:
    if outputfile != " ":
        fout = topoheaderwrite(topoheader, outputfile, closefile=False)
        for i in range(topoheader["nrows"]):
            for j in range(topoheader["ncols"]):
                fout.write("%s\n" % Z[i, j])
        fout.close()
    return (X, Y, Z)
    # end scatter2gridded===================================================


# ============================================================================
def topoheaderwrite(topoheader, outputfile, closefile=True):

    """
    topoheaderwrite(topoheader,outputfile) opens an ascii topography data file and writes the header
    using the dictionary "topoheader"

    The header is of the following form with columns containing the topoheader value and key respectively.

         int ncols
         int nrows
         float xll
         float yll
         float cellsize
         float nodata_value


    if closefile==True: the file is closed. Otherwise return the open file object.
    """

    fout = open(outputfile, "w")

    fout.write("%s %s\n" % (topoheader["ncols"], "ncols"))
    fout.write("%s %s\n" % (topoheader["nrows"], "nrows"))
    fout.write("%s %s\n" % (float(topoheader["xll"]), "xll"))
    fout.write("%s %s\n" % (float(topoheader["yll"]), "yll"))
    fout.write("%s %s\n" % (float(topoheader["cellsize"]), "cellsize"))
    fout.write("%s %s\n" % (topoheader["nodata_value"], "nodata_value"))
    if closefile:
        fout.close()
    else:
        return fout
    # end headerwriter=========================================================================


# ============================================================================
def esriheaderwrite(topoheader, outputfile, closefile=True):

    """
    esriheaderwrite(topoheader,outputfile) opens an ascii topography data file and writes the header
    using the dictionary "topoheader"

    The header is of the following form with columns containing the topoheader key and value respectively.

         NCOLS int
         NROWS int
         XLLCORNER float
         YLLCORNER float
         CELLSIZE float
         NODATA_VALUE float


    if closefile==True: the file is closed. Otherwise return the open file object.
    """

    fout = open(outputfile, "w")

    fout.write("%s %s\n" % ("NCOLS", topoheader["ncols"]))
    fout.write("%s %s\n" % ("NROWS", topoheader["nrows"]))
    fout.write("%s %s\n" % ("XLLCORNER", float(topoheader["xll"]))) # KRB NOTE: I think this should be xllcenter
    fout.write("%s %s\n" % ("YLLCORNER", float(topoheader["yll"])))
    fout.write("%s %s\n" % ("CELLSIZE", float(topoheader["cellsize"])))
    fout.write("%s %s\n" % ("NODATA_VALUE", topoheader["nodata_value"]))
    if closefile:
        fout.close()
    else:
        return fout
    # end headerwriter=========================================================================


# =========================================================================================
def topoheaderread(inputfile, closefile=True):

    """
    topoheaderread (inputfile):
    read the header in inputfile and place in dictionary topoheader to be returned.

    The header is of the following form with columns containing the topoheader value and keyword respectively.

         int ncols
         int nrows
         float xll
         float yll
         float cellsize
         float nodata_value
    """
    topoheader = {
        "ncols": 0,
        "nrows": 0,
        "xll": 0.0,
        "yll": 0.0,
        "cellsize": 0.0,
        "nodata_value": 0,
    }
    keylist = list(topoheader.keys())

    keymap = {
        "ncols": "ncols",
        "nrows": "nrows",
        "xll": "xll",
        "yll": "yll",
        "cellsize": "cellsize",
        "nodata_value": "nodata_value",
        "xllcenter": "xll",
        "yllcenter": "yll",
        "xllcorner": "xll",
        "yllcorner": "yll",
        "xlower": "xll",
        "ylower": "yll",
    }

    fid = open(inputfile, "r")
    keyleft = len(keylist)
    while keyleft > 0:
        line = fid.readline().split()
        if line:
            if line[0].lower() in list(keymap.keys()):
                topoheader[keymap[line[0].lower()]] = iotools.convertd2e(line[1])
                keyleft = keyleft - 1
            if line[1].lower() in list(keymap.keys()):
                topoheader[keymap[line[1].lower()]] = iotools.convertd2e(line[0])
                keyleft = keyleft - 1

    # check if passes convert strings values to numeric
    for key in keylist:
        if not key in topoheader:
            print(("ERROR: topoheader not fully specified in %s" % (inputfile)))
            exit
        else:
            if (
                "." in topoheader[key]
                or "nan" in topoheader[key].lower()
                or "e" in topoheader[key].lower()
            ):
                topoheader[key] = float(topoheader[key])
            else:
                topoheader[key] = int(topoheader[key])

    if closefile:
        fid.close()
        return topoheader
    else:
        return (fid, topoheader)

    # end topoheader================================================================================


# ==================================================================================================
def topofile2griddata(inputfile, topotype=2):
    """
    topofile2griddata (inputfile):
    read topofile into a numpy array.

    read data in topo files of type 1, 2 or 3 into numpy arrays
    X,Y, Z, each with shape=(nrows,ncols) holding x,y and z coords.

    """
    # import pylab

    if topotype > 1:
        (fin, topoheader) = topoheaderread(inputfile, closefile=False)
        zdata = fin.readlines()
        fin.close()
        for row in range(len(zdata)):
            zdata[row] = iotools.convertd2e(zdata[row]).split()
            for col in range(len(zdata[row])):
                zdata[row][col] = float(zdata[row][col])

        Z = np.array(zdata)
        Z = np.reshape(Z, (topoheader["nrows"], topoheader["ncols"]))

        xlower = topoheader["xll"]
        xupper = xlower + topoheader["cellsize"] * (topoheader["ncols"] - 1)

        ylower = topoheader["yll"]
        yupper = ylower + topoheader["cellsize"] * (topoheader["nrows"] - 1)

        x = np.linspace(xlower, xupper, topoheader["ncols"])
        y = np.linspace(ylower, yupper, topoheader["nrows"])
        [X, Y] = np.meshgrid(x, y)
        Y = np.flipud(Y)
    else:
        a = iotools.datafile2array(inputfile)
        xdiff = np.diff(a[:, 0])
        # inddiff=pylab.find(xdiff<0)
        inddiff = (xdiff < 0).np.argmax()
        xlength = inddiff[0] + 1
        ylength = len(a[:, 0]) / xlength
        x = a[:, 0]
        y = a[:, 1]
        z = a[:, 2]

        X = np.reshape(x, (ylength, xlength))
        Y = np.reshape(y, (ylength, xlength))
        Z = np.reshape(z, (ylength, xlength))

    return X, Y, Z
    # end topofile2griddata ======================================================================


# ==================================================================================================
def griddata2topofile(
    X, Y, Q, outputfile, topotype=2, nodata_value_in=9999.0, nodata_value_out=9999.0
):
    """
    griddata2topofile takes gridded data and produces a topofile with a header

    X, Y are expected to reflect the grid cell centers. The lower left corner
    will be inferred and written to the header.

    Q is expected to be in the shape [meqn, nrow, ncol] and will be written
    to meqn bands.

    """

    nrows = len(Z[:, 0])
    ncols = len(Z[0, :])
    xllcc = X[0, 0] # lower left cell center
    yllcc = Y[-1, 0]
    nodata_value = nodata_value_out
    xuppercc = X[0, -1] # upper right cell center
    yuppercc = Y[0, 0]

    if yuppercc < yllcc:
        print("geotools.topotools.griddata2topofile:")
        print("ERROR: griddata is not in the proper format: Y[0,0]<Y[-1,0] ")
        print("The matrix Y, should advance from north to south rowwise")

    cellsizeX = (xuppercc - xllcc) / (ncols - 1) # this diff is correct if cell centers are used.
    cellsizeY = (yuppercc - yllcc) / (nrows - 1) # because the distance between the cell centers is
    # the total number of rows/columns minus one.

    # calculate the lower left corner location.
    xll = xllcc - 0.5 * cellsizeX
    yll = yllcc - 0.5 * cellsizeY

    topoheader = {}
    topoheader["nrows"] = nrows
    topoheader["ncols"] = ncols
    topoheader["xll"] = xll
    topoheader["yll"] = yll
    topoheader["cellsize"] = cellsizeX
    topoheader["nodata_value"] = nodata_value_out

    if (abs(cellsizeX - cellsizeY) < -1.0e-9) & (topotype > 1):
        print("geotools.topotools.griddata2topofile:")
        print("WARNING: cellsize is not uniform in x and y")
        print(("cellsize in the x-direction %s" % cellsizeX))
        print(("cellsize in the y-direction %s" % cellsizeY))
        print("Consider changing to topotype=1")

    if topotype == 2:
        fout = topoheaderwrite(topoheader, outputfile, closefile=False)
        for i in range(nrows):
            for j in range(ncols):
                fout.write("%s\n" % (Z[i, j]))
        fout.close()

    elif topotype == 3:
        fout = topoheaderwrite(topoheader, outputfile, closefile=False)
        for i in range(nrows):
            for j in range(ncols):
                fout.write("%s   " % (Z[i, j]))
            fout.write("\n")
        fout.close()

    else:
        fout = open(outputfile, "w")
        for i in range(nrows):
            for j in range(ncols):
                fout.write("%s %s %s\n" % (X[i, j], Y[i, j], Z[i, j]))
        fout.close()

    # end griddata2topofile ======================================================================
    # end griddata2topofile ======================================================================


def griddata2gtif(
    X, Y, Q, outputfile, nodata_value_in=9999.0, nodata_value_out=9999.0, epsg=None
):
    """
    griddata2gtif takes gridded data and produces a geotif

    """
    try:
        import rasterio
        import rasterio.crs
        import rasterio.transform
    except ImportError:
        raise ImportError("rasterio needed for griddata2gtif")

    nrows = len(X[:, 0])
    ncols = len(X[0, :])
    meqn = Q.shape[0]
    xllcc = X[0, 0]
    yllcc = Y[-1, 0]
    nodata_value = nodata_value_out
    xuppercc = X[0, -1]
    yuppercc = Y[0, 0]

    if yuppercc < yllcc:
        print("geotools.topotools.griddata2topofile:")
        print("ERROR: griddata is not in the proper format: Y[0,0]<Y[-1,0] ")
        print("The matrix Y, should advance from north to south rowwise")

    cellsizeX = (xuppercc - xllcc) / (ncols - 1)
    cellsizeY = (yuppercc - yllcc) / (nrows - 1)

    # define rasterio profile
    out_profile = {}
    out_profile["transform"] = rasterio.transform.from_bounds(
        xllcc - cellsizeX / 2,
        yllcc - cellsizeX / 2,
        xuppercc + cellsizeX / 2,
        yuppercc + cellsizeX / 2,
        ncols,
        nrows,
    ) # rasterio transform is based on lower left corner of lower left grid
    # cell, X and Y used here are cell centers.

    out_profile["height"], out_profile["width"] = X.shape
    out_profile["dtype"] = "float32"
    out_profile["count"] = meqn
    out_profile["driver"] = "GTiff"
    out_profile["nodata"] = nodata_value_out
    if epsg is not None:
        out_profile["crs"] = rasterio.crs.CRS.from_epsg(epsg)

    if abs(cellsizeX - cellsizeY) < -1.0e-9:
        print("geotools.topotools.griddata2topofile:")
        print("WARNING: cellsize is not uniform in x and y")
        print(("cellsize in the x-direction %s" % cellsizeX))
        print(("cellsize in the y-direction %s" % cellsizeY))
        print("Consider changing to topotype=1")

    with rasterio.open(outputfile, "w", **out_profile) as dst:
        for i in range(meqn):

            # get band values
            band = i + 1
            vals = (Q[i, :, :]).reshape((nrows, ncols)).astype("float32")

            # remap nodata if necessary
            if nodata_value_in != nodata_value_out:
                nodata = vals == nodata_value_in
                vals[nodata] = nodata_value_out

            # write to band.
            dst.write(vals, band)

    # end griddata2gtof ======================================================================


# ================================================================================================
def converttopotype(
    inputfile, outputfile, topotypein=1, topotypeout=2, nodata_value=None
):
    """
    convert topofiles of one type to another.
    """

    (X, Y, Z) = topofile2griddata(inputfile, topotypein)

    if topotypein > 1 and not nodata_value:
        topoheader = topoheaderread(inputfile)
        nodata_value = topoheader["nodata_value"]
    if topotypein == 1 and topotypeout > 1 and not nodata_value:
        print("You must provide a value for nodata_value")

    griddata2topofile(X, Y, Z, outputfile, topotypeout, nodata_value, nodata_value)

    # end converttopotype ==========================================================================


# ==================================================================================================
def griddatasubset(X, Y, Z, xlow=-1.0e6, xhi=1.0e6, ylow=-1.0e6, yhi=1.0e6):
    """
    griddatasubset takes grided data (X,Y,Z) and creates a subset of new gridded data

    X,Y,Z are assumed to be numpy arrays where data advances from northwest---northeast then
    southward, corresponding to advancing across columns then down rows.

    the new gridded data will correspond to the largest subset of the region [xlow,xhi] X [ylow,yhi]
    """

    xind = np.where((X[0, :] >= xlow) & (X[0, :] <= xhi))[0]
    yind = np.where((Y[:, 0] <= yhi) & (Y[:, 0] >= ylow))[0]

    Xsub = X[np.ix_(yind, xind)]
    Ysub = Y[np.ix_(yind, xind)]
    Zsub = Z[np.ix_(yind, xind)]

    return Xsub, Ysub, Zsub
    # end griddatasubset ==========================================================================


# ==================================================================================================
def topofilefindz(pts, inputfile, topotypein=2):
    """
    topofilefindz takes an inputfile, and the coordinates of multiple points, as a list of pairs,
    pts=[(x1,y1),...,(xn,yn)] or a numpy array of shape (n,2) [[x1,y1],...[xn,yn]], etc.
    and returns the topo z values as a numpy list z = [z1,...,zn].
    at those coordinates. It interpolates a bilinear function between the 4 nodes surrounding (x,y).

    """
    if isinstance(inputfile, str):
        (X, Y, Z) = topofile2griddata(inputfile, topotypein)
    else:
        (X, Y, Z) = inputfile

    z = []

    for i in range(len(pts)):
        x = pts[i][0]
        y = pts[i][1]

        if (x < X[0, 0]) | (x > X[0, -1]) | (y < Y[-1, 0]) | (y > Y[0, 0]):
            print(
                (
                    "WARNING: point %i is outside data file: (x,y)= (%g,%g)"
                    % (i + 1, x, y)
                )
            )
            print(
                (
                    "**file corners are (X0,Y0)= (%g,%g), and (X1,Y1) = (%g,%g)"
                    % (X[0, 0], Y[-1, -1], X[-1, -1], Y[0, 0])
                )
            )
            z.append(np.nan)
        else:

            # find indices of four corners
            # some corners might be the same, if x or y happen to intersect X or Y
            i0 = np.where(X[0, :] <= x)[0][-1]
            i1 = np.where(X[0, :] >= x)[0][0]

            j0 = np.where(Y[:, 0] <= y)[0][0]
            j1 = np.where(Y[:, 0] >= y)[0][-1]

            # find height of four corners
            Z00 = Z[j0, i0]
            Z01 = Z[j0, i1]
            Z10 = Z[j1, i0]
            Z11 = Z[j1, i1]

            X00 = X[j0, i0]
            X01 = X[j0, i1]
            X10 = X[j1, i0]
            X11 = X[j1, i1]

            Y00 = Y[j0, i0]
            Y01 = Y[j0, i1]
            Y10 = Y[j1, i0]
            Y11 = Y[j1, i1]

            # find slopes of opposing lines.
            if i0 == i1:
                dzdx0 = 0.0
                dzdx1 = 0.0
            else:
                dzdx0 = (Z01 - Z00) / (X11 - X00)
                dzdx1 = (Z11 - Z10) / (X11 - X00)

            # find height of points on lines
            zy0 = Z00 + (x - X00) * dzdx0
            zy1 = Z10 + (x - X10) * dzdx1

            if j0 == j1:
                dzdy = 0.0
            else:
                dzdy = (zy1 - zy0) / (Y11 - Y00)

            z.append(zy0 + (y - Y00) * dzdy)

    z = np.array(z)
    return z


# ==================================================================================================
def griddatafindz(pts, X, Y, Z):
    """
    griddatafindz takes gridded data, and the coordinates of multiple points, as a list of pairs,
    pts=[(x1,y1),...,(xn,yn)] or a numpy array of shape (n,2) [[x1,y1],...[xn,yn]], etc.
    and returns the topo z values as a numpy list z = [z1,...,zn].
    at those coordinates. It interpolates a bilinear function between the 4 nodes surrounding (x,y).

    """

    z = []

    for i in range(len(pts)):
        x = pts[i][0]
        y = pts[i][1]

        if (x < X[0, 0]) | (x > X[0, -1]) | (y < Y[-1, 0]) | (y > Y[0, 0]):
            print(
                (
                    "WARNING: point %i is outside data file: (x,y)= (%g,%g)"
                    % (i + 1, x, y)
                )
            )
            print(
                (
                    "**file corners are (X0,Y0)= (%g,%g), and (X1,Y1) = (%g,%g)"
                    % (X[0, 0], Y[-1, -1], X[-1, -1], Y[0, 0])
                )
            )
            z.append(-9999)
        else:

            # find indices of four corners
            # some corners might be the same, if x or y happen to intersect X or Y
            i0 = np.where(X[0, :] <= x)[0][-1]
            i1 = np.where(X[0, :] >= x)[0][0]

            j0 = np.where(Y[:, 0] <= y)[0][0]
            j1 = np.where(Y[:, 0] >= y)[0][-1]

            # find height of four corners
            Z00 = Z[j0, i0]
            Z01 = Z[j0, i1]
            Z10 = Z[j1, i0]
            Z11 = Z[j1, i1]

            X00 = X[j0, i0]
            X01 = X[j0, i1]
            X10 = X[j1, i0]
            X11 = X[j1, i1]

            Y00 = Y[j0, i0]
            Y01 = Y[j0, i1]
            Y10 = Y[j1, i0]
            Y11 = Y[j1, i1]

            # find slopes of opposing lines.
            if i0 == i1:
                dzdx0 = 0.0
                dzdx1 = 0.0
            else:
                dzdx0 = (Z01 - Z00) / (X11 - X00)
                dzdx1 = (Z11 - Z10) / (X11 - X00)

            # find height of points on lines
            zy0 = Z00 + (x - X00) * dzdx0
            zy1 = Z10 + (x - X10) * dzdx1

            if j0 == j1:
                dzdy = 0.0
            else:
                dzdy = (zy1 - zy0) / (Y11 - Y00)

            z.append(zy0 + (y - Y00) * dzdy)

    z = np.array(z)
    return z


# ==================================================================================================
def topofilesubset(
    inputfile,
    outputfile,
    topotypein=2,
    topotypeout=2,
    xlow=-1.0e6,
    xhi=1.0e6,
    ylow=-1.0e6,
    yhi=1.0e6,
    nodata_value_in=None,
    cheap=False,
):
    """
    topofilesubset takes a topofile, takes a subset of the data and produces a new topofile.

    If cheap = True then the data is directly read from one file and written to the smaller file
    This is useful for very large topofiles that are being split into more manageable files.

    """

    if cheap == False:
        # this requires too much memory for some large files
        # use cheap option if topotype>1
        (X, Y, Z) = topofile2griddata(inputfile, topotypein)
        if topotypein > 1 and not nodata_value_in:
            topoheader = topoheaderread(inputfile)
            nodata_value_in = topoheader["nodata_value"]

        if topotypein == 1 and topotypeout > 1 and not nodata_value_in:
            print("You must provide a value for nodata_value_in")

        nodata_value_out = nodata_value_in
        (Xsub, Ysub, Zsub) = griddatasubset(X, Y, Z, xlow, xhi, ylow, yhi)
        griddata2topofile(
            Xsub, Ysub, Zsub, outputfile, topotypeout, nodata_value_in, nodata_value_out
        )

    else:
        if topotypein == 1:
            print("geotools.topotools.topofilesubset")
            print("ERROR: topotype=1 not supported in cheap mode")
            print("convert the input file to topotype 2 or 3")
            print("with converttopotype")
            return

        (fidin, topoheaderin) = topoheaderread(inputfile, False)
        nodata_value_in = topoheaderin["nodata_value"]
        ncols = topoheaderin["ncols"]
        nrows = topoheaderin["nrows"]
        yll = topoheaderin["yll"]
        xll = topoheaderin["xll"]
        cellsize = topoheaderin["cellsize"]
        yupper = yll + cellsize * (nrows - 1)
        xupper = xll + cellsize * (ncols - 1)

        xupperout = min(xupper, xhi)
        xlowout = max(xlow, xll)
        yupperout = min(yupper, yhi)
        ylowout = max(yll, ylow)

        theadout = {}
        ncolsout = int((xupperout - xlowout) / cellsize + 1)
        nrowsout = int((yupperout - ylowout) / cellsize + 1)
        j = np.ceil((xlowout - xll) / cellsize + 1)
        xllout = xll + (j - 1) * cellsize
        i = np.ceil((ylowout - yll) / cellsize + 1)
        yllout = yll + (i - 1) * cellsize

        theadout["xll"] = xllout
        theadout["yll"] = yllout
        theadout["ncols"] = ncolsout
        theadout["nrows"] = nrowsout
        theadout["cellsize"] = cellsize
        theadout["nodata_value"] = nodata_value_in

        fidout = topoheaderwrite(theadout, outputfile, closefile=False)
        outpts = ncolsout * nrowsout
        writtenpts = 0

        if topotypein > 1:
            while outpts > 0:
                for row in range(nrows):
                    y = yupper - row * cellsize
                    for col in range(ncols):
                        x = xll + col * cellsize
                        zdata = fidin.readline().split()
                        w = writtenpts
                        for jj in range(len(zdata)):
                            if (xlow <= x <= xhi) & (ylow <= y < yhi):
                                fidout.write("%s  " % zdata[jj])
                                outpts = outpts - 1
                                writtenpts = writtenpts + 1
                        if writtenpts > w:
                            fidout.write("\n")

            if writtenpts != ncolsout * nrowsout:
                print("geotools.topotools.topofilesubset")
                print("ERROR: points written != ncols*nrows in header")

        fidout.close()
        fidin.close()
    # end topofilesubset==========================================================================


# ==================================================================================================
def topofilesubsample(
    inputfile,
    outputfile,
    sampleinteger,
    topotypein=2,
    topotypeout=2,
    nodata_value_in=None,
):
    """
    topofilesubsample takes a topofile, and resamples the data at an integer (sampleinteger)
     number of grid points to produces a new topofile.

    For example, if a topofile contains 1m data, if the integer is 10, the resulting
     file will be 10m data.

    This is useful for shrinking huge DEMs where high accuracy is not needed.

    """

    (X, Y, Z) = topofile2griddata(inputfile, topotypein)
    if topotypein > 1 and not nodata_value_in:
        topoheader = topoheaderread(inputfile)
        nodata_value_in = topoheader["nodata_value"]

    if topotypein == 1 and topotypeout > 1 and not nodata_value_in:
        print("You must provide a value for nodata_value_in")

    nodata_value_out = nodata_value_in
    Xsub = X[0::sampleinteger, 0::sampleinteger]
    Ysub = Y[0::sampleinteger, 0::sampleinteger]
    Zsub = Z[0::sampleinteger, 0::sampleinteger]
    griddata2topofile(
        Xsub, Ysub, Zsub, outputfile, topotypeout, nodata_value_in, nodata_value_out
    )


# ================================================================================================


def topofileinterpolate(
    inputfile, outputfile, lrat=None, xi=[], yi=[], topotype=2, kx=1, ky=1, s=0.0
):

    """
    takes a topofile and interpolates it to a new (presumably finer) grid defined by xi,yi
    or simply a refinement ratio lrat
    outputs a new topofile of the same topotype
    routine uses scipy bilinear RectBivariateSpline
    kx, ky, s (input to RectBivariateSpline...see docs)
    """
    from scipy import interpolate

    if topotype > 1:
        topoheader = topoheaderread(inputfile)
        nodata_valuein = topoheader["nodata_value"]
    else:
        print("topotype 1 not supported. Convert the input file")

    (X, Y, Z) = topofile2griddata(inputfile, topotype)
    Y = np.flipud(Y)
    Z = np.flipud(Z)

    if (not xi) | (not yi):
        try:
            lrat
        except NameError:
            err_msg = "Error: you must call with a refinement ratio or x and y coordinate arrays"
            raise Exception(err_msg)
    if lrat:
        xlen = (np.shape(X)[1] - 1) * lrat + 1
        ylen = (np.shape(Y)[0] - 1) * lrat + 1

        xi = np.linspace(X[0, 0], X[0, -1], xlen)
        yi = np.linspace(Y[0, 0], Y[-1, 0], ylen)

    x = X[0, :]
    y = Y[:, 0]

    sp = interpolate.RectBivariateSpline(y, x, Z, kx=kx, ky=ky, s=s)
    # sp = interpolate.interp2d(x,y,Z,kind=kind)

    Zi = sp(yi, xi)
    (Xi, Yi) = np.meshgrid(xi, yi)
    Yi = np.flipud(Yi)
    Zi = np.flipud(Zi)
    # import pdb;pdb.set_trace()
    griddata2topofile(
        Xi,
        Yi,
        Zi,
        outputfile,
        topotype,
        nodata_value_in=nodata_valuein,
        nodata_value_out=nodata_valuein,
    )


# ===============================================================================
def scatter2smoothgridded(
    outputfile,
    headerfile=None,
    xi=[],
    yi=[],
    inputfile=None,
    x=[],
    y=[],
    z=[],
    topotype=2,
    kx=3,
    ky=3,
    s=0,
):

    """
    interpolate scattered data to gridded data using a smoothed bivariate spline of order kx,ky
    note: this will heavily smooth a complicated DEM but can be of use for
    new grid defined by uniformly spaced xi, yi or a header file
    input data can be x,y,z arrays or an .xyz 3 column file
    """

    from scipy import interpolate

    if (not x) | (not y) | (not z):
        try:
            inputfile
        except NameError:
            err_msg = "Error: you must call with either a data file or x,y,z arrays"
            raise Exception(err_msg)

    if (not xi) | (not yi):
        try:
            headerfile
        except NameError:
            err_msg = "Error: you must call with either a header file or xi,yi coordinate arrays"
            raise Exception(err_msg)

    if inputfile:
        xyz = np.loadtxt(inputfile)
        x = xyz[:, 0]
        y = xyz[:, 1]
        z = xyz[:, 2]

    if headerfile:
        # determine what the output grid will look like from headerfile
        topoheader = topoheaderread(inputfile=headerfile)
        # Create the gridded data using pylab "griddata function."
        xi = np.arange(
            topoheader["xll"],
            topoheader["xll"] + topoheader["ncols"] * topoheader["cellsize"],
            step=topoheader["cellsize"],
            dtype=float,
        )
        yi = np.arange(
            topoheader["yll"],
            topoheader["yll"] + topoheader["nrows"] * topoheader["cellsize"],
            step=topoheader["cellsize"],
            dtype=float,
        )

    w = np.ones(np.shape(x)) / np.shape(x)
    sp = interpolate.SmoothBivariateSpline(y, x, z, w=w, kx=kx, ky=ky, s=s)
    Zi = sp(yi, xi)

    (Xi, Yi) = np.meshgrid(xi, yi)
    Yi = np.flipud(Yi)
    Zi = np.flipud(Zi)
    griddata2topofile(Xi, Yi, Zi, outputfile, topotype)


# ==================================================================================================
def griddatasubsample(X, Y, Z, sampleinteger):
    """
    topofilesubsample takes a topofile, and resamples the data at an integer (sampleinteger)
     number of grid points to produces a new topofile.

    For example, if a topofile contains 1m data, if the integer is 10, the resulting
     file will be 10m data.

    This is useful for shrinking huge DEMs where high accuracy is not needed.

    """

    Xsub = X[0::sampleinteger, 0::sampleinteger]
    Ysub = Y[0::sampleinteger, 0::sampleinteger]
    Zsub = Z[0::sampleinteger, 0::sampleinteger]

    return Xsub, Ysub, Zsub


# ================================================================================================
def removenodata_value(
    inputfile, outputfile, topotypein=2, topotypeout=2, nodata_value=None, method="fill"
):
    """
    remove the nodata_values in a topo file by interpolating from meaningful values.
    """
    import pylab

    (X, Y, Z) = topofile2griddata(inputfile, topotypein)

    if topotypein > 1 and not nodata_value:
        topoheader = topoheaderread(inputfile)
        nodata_value = topoheader["nodata_value"]
    elif not nodata_value:
        print("provide a value for nodata_value when using topotype1")

    if method == "fill":
        ind = fixdata.findbadindices(Z, nodata_value)
        if size(ind) > 0:
            print(("Changing %s nodata_value points" % size(ind)))
        Z = fixdata.fillbaddata(Z, ind)
        griddata2topofile(X, Y, Z, outputfile, topotypeout, nodata_value, nodata_value)
        return
    nrows = shape(Z)[0]
    ncols = shape(Z)[1]
    npts = nrows * ncols

    xi = X[0, :]
    yi = Y[:, 0]

    X.np.reshape(npts)
    Y.np.reshape(npts)
    Z.np.reshape(npts)

    ind = np.where(Z != nodata_value)
    X = X[ind]
    Y = Y[ind]
    Z = Z[ind]

    ptsremove = npts - len(Z)
    if ptsremove > 0:
        print(("Removing %s nodata_value points" % ptsremove))

    Z = pylab.griddata(X, Y, Z, xi, yi)
    (X, Y) = np.meshgrid(xi, yi)

    griddata2topofile(X, Y, Z, outputfile, topotypeout, nodata_value, nodata_value)

    return

    # end removenodata_value ======================================================================


# =================================================================================================
def changenodata_value(
    inputfile,
    outputfile,
    topotypein,
    topotypeout=None,
    nodata_valuein=None,
    nodata_valueout=np.nan,
):
    """
    change the nodata_values in a topo file by interpolating from meaningful values.
    """

    (X, Y, Z) = topofile2griddata(inputfile, topotypein)

    if topotypein > 1 and not nodata_valuein:
        topoheader = topoheaderread(inputfile)
        nodata_valuein = topoheader["nodata_value"]
    elif not nodata_valuein:
        print("provide a value for nodata_valuein when using topotype1")

    if not topotypeout:
        topotypeout = topotypein

    nrows = shape(Z)[0]
    ncols = shape(Z)[1]
    npts = nrows * ncols

    ind = np.where(Z == nodata_valuein)
    Z[ind] = nodata_valueout

    if size(ind) > 0:
        print(("Changing %s nodata_value points" % size(ind)))

    griddata2topofile(X, Y, Z, outputfile, topotypeout, nodata_valuein, nodata_valueout)

    return

    # end removenodata_value =================================================================


# ============================================================================================
def burnin_nodata_value(
    inputfile1,
    inputfile2,
    outputfile,
    topotypein1=3,
    topotypein2=3,
    topotypeout=None,
    nodata_valuein=None,
):

    """
    create a topo file from 2 others using values from secondary file
     for burned out values in primaryfile

    inputfile1: name of primary topo file (the preferred data where it exists)
    inputfile2: name of secondary topo file (data to be used where primary file has nodata_values)
    outputfile: output topo file (burned in)
    """

    (X, Y, Z) = topofile2griddata(inputfile1, topotypein1)

    Znew = Z

    Znew = Z

    if topotypein1 > 1 and not nodata_valuein:
        topoheader = topoheaderread(inputfile1)
        nodata_valuein = topoheader["nodata_value"]
    elif not nodata_valuein:
        print("provide a value for nodata_valuein when using topotype1")

    if not topotypeout:
        topotypeout = topotypein1

    nrows = np.shape(Z)[0]
    ncols = np.shape(Z)[1]
    npts = nrows * ncols

    ind = np.where((Z == np.real(nodata_valuein) | (Z == int(nodata_valuein))))
    # import pdb; pdb.set_trace()

    pts = []

    for i in range(len(ind[0])):
        x = X[ind[0][i], ind[1][i]]
        y = Y[ind[0][i], ind[1][i]]
        pts.append((x, y))

    z = topofilefindz(pts, inputfile2, topotypein2)

    for i in range(len(ind[0])):
        Znew[ind[0][i], ind[1][i]] = z[i]

    griddata2topofile(
        X, Y, Znew, outputfile, topotypeout, nodata_valuein, nodata_valuein
    )


# ============================================================================================

# ============================================================================================
def merge_topofiles(
    X,
    Y,
    inputfile1,
    inputfile2,
    outputfile,
    topotypein1=2,
    topotypein2=2,
    topotypeout=None,
    nodata_valuein=None,
):

    """
    create a topo file from 2 others, given preference of files and input parameters specifying output grid

    X,Y: gridded arrays for output file, eg. from meshgrid.
    inputfile1: name of primary topo file (the preferred data where it exists)
    inputfile2: name of secondary topo file (data to be used where primary file has nodata_values, or no values)
    outputfile: output topo file
    """

    Z = np.ones(np.shape(X))

    Z = np.ones(np.shape(X))

    (X1, Y1, Z1) = topofile2griddata(inputfile1, topotypein1)
    (X2, Y2, Z2) = topofile2griddata(inputfile2, topotypein2)

    xl1 = X1[0, 0]
    xu1 = X1[-1, -1]
    yl1 = Y1[-1, -1]
    yu1 = Y1[0, 0]

    if topotypein1 > 1 and not nodata_valuein:
        topoheader = topoheaderread(inputfile1)
        nodata_valuein = topoheader["nodata_value"]
    elif not nodata_valuein:
        print("provide a value for nodata_valuein when using topotype1")

    if not topotypeout:
        topotypeout = topotypein1

    nrows = np.shape(Z)[0]
    ncols = np.shape(Z)[1]

    for i in range(nrows):
        for j in range(ncols):
            x = X[i, j]
            y = Y[i, j]

            if (x >= xl1) & (x <= xu1) & (y >= yl1) & (y <= yu1):
                z = griddatafindz([(x, y)], X1, Y1, Z1)
                if abs(z - nodata_valuein) < 1.0:
                    z = griddatafindz([(x, y)], X2, Y2, Z2)
                Z[i, j] = z
            else:
                Z[i, j] = griddatafindz([(x, y)], X2, Y2, Z2)

    # import pdb; pdb.set_trace()

    griddata2topofile(X, Y, Z, outputfile, topotypeout, nodata_valuein, nodata_valuein)


# ============================================================================================
def clip_surface(
    inputfile1,
    inputfile2,
    outputfile,
    topotypein1=3,
    topotypein2=3,
    topotypeout=None,
    nodata_valuein=None,
):

    """
    create a surface file from 2 others using values in the primary file where they are
    not clipped in the secondary file. Clipping values where they are clipped in the secondary.
    (eg. primary file is original topo (top surface) secondary file is a clipped slip surface)

    useful for creating a top surface over a slip surface and negative nodata_values outside of slip surface

    inputfile1: name of primary topo file (the non-clipped data)
    inputfile2: name of secondary topo file (clipped data will be clipped in primary file)
    outputfile: output topo file (clipped)
    """

    (X, Y, Z) = topofile2griddata(inputfile1, topotypein1)
    (X2, Y2, Z2) = topofile2griddata(inputfile2, topotypein2)

    if topotypein2 > 1 and not nodata_valuein:
        topoheader = topoheaderread(inputfile2)
        nodata_valuein = topoheader["nodata_value"]
    elif not nodata_valuein:
        print("provide a value for nodata_valuein when using topotype1")

    if not topotypeout:
        topotypeout = topotypein1

    nrows = np.shape(Z2)[0]
    ncols = np.shape(Z2)[1]
    npts = nrows * ncols

    # import pdb;pdb.set_trace()
    ind = np.where((Z2 != np.real(nodata_valuein)) & (Z2 != int(nodata_valuein)))
    # import pdb; pdb.set_trace()

    pts = []

    for i in range(len(ind[0])):
        x = X2[ind[0][i], ind[1][i]]
        y = Y2[ind[0][i], ind[1][i]]
        pts.append((x, y))

    z = topofilefindz(pts, inputfile1, topotypein1)

    for i in range(len(ind[0])):
        Z2[ind[0][i], ind[1][i]] = z[i]

    griddata2topofile(
        X2, Y2, Z2, outputfile, topotypeout, nodata_valuein, nodata_valuein
    )


# ============================================================================================
def swapheader(inputfile, outputfile):
    """
    take a topo file and swap the order of key and value in header so that value is in the
    first column and key in the second.
    """

    (fidin, header) = topoheaderread(inputfile, closefile=False)
    fidout = topoheaderwrite(header, outputfile, closefile=False)
    while True:
        line = fidin.readline()
        if not line:
            break
        fidout.write(line)

    fidin.close()
    fidout.close()

    return
    # =========================================================================================


# ============================================================================================
def esriheader(inputfile, outputfile):
    """
    take a topotype file and swap the order of key and value in header so that header is a
    standard esri header with key in the first column
    """

    (fidin, header) = topoheaderread(inputfile, closefile=False)
    fidout = esriheaderwrite(header, outputfile, closefile=False)
    while True:
        line = fidin.readline()
        if not line:
            break
        fidout.write(line)

    fidin.close()
    fidout.close()

    return
    # =========================================================================================


def topoboundary(infile):
    """
    simple script to return the boundary coordinates of a topofile.
    useful to quickly calculate the upper extents
    """
    (fidin, header) = topoheaderread(infile, closefile=False)

    xll = header["xll"]
    yll = header["yll"]
    dx = header["cellsize"]
    mx = header["ncols"]
    my = header["nrows"]

    xur = xll + (mx - 1) * dx
    yur = yll + (my - 1) * dx

    print(("xll = %s, xur = %s, yll = %s, yur = %s" % (xll, xur, yll, yur)))

    return [xll, xur, yll, yur]


# ==============================================================================
def create_topo_func(loc, verbose=False):
    """Given a set of (x,z) locations, create a lambda function

    Create a lambda function that when evaluated will give the topgraphy
    height at the point (x,y).

    :Example:
    >>> f = create_topo_profile_func(loc)
    >>> b = f(x,y)

    :Input:
     - *loc* (list) - Create a topography file with the profile denoted by the
       tuples inside of loc.  A sample set of points are shown below.  Note
       that the first value of the list is the x location and the second is
       the height of the topography.

        z (m)
        ^                                                  o loc[5]  o
        |
        |                                          loc[4]
        |--------------------------------------------o-----> x (m) (sea level)
        |
        |                                o loc[2] o loc[3]
        |
        |
        |                           o loc[1]
        |
        |
        |__________________o loc[0]
        0.0


    """

    cmd_str = "lambda x,y: (x <= %s) * %s" % (loc[0][0], loc[0][1])
    for i in range(0, len(loc) - 1):
        loc_str = " + (%s < x) * (x <= %s)" % (loc[i][0], loc[i + 1][0])
        loc_str = "".join((loc_str, " * ((%s - %s) " % (loc[i][1], loc[i + 1][1])))
        loc_str = "".join((loc_str, " / (%s - %s)" % (loc[i][0], loc[i + 1][0])))
        loc_str = "".join((loc_str, " * (x - %s) + %s)" % (loc[i][0], loc[i][1])))
        cmd_str = "".join((cmd_str, loc_str))
    cmd_str = "".join((cmd_str, " + (%s < x) * %s" % (loc[-1][0], loc[-1][1])))

    if verbose:
        print(cmd_str)
    return eval(cmd_str)


# Generic, spheroid based conversion
# TODO: Convert this to using the basemap package instead
deg2meters = (
    lambda theta, lat: R_earth * theta * np.pi / 180.0 * np.cos(lat * np.pi / 180.0)
)
meters2deg = lambda d, lat: d / (R_earth * np.pi / 180.0 * np.cos(lat * np.pi / 180.0))

# Based at lat = 24 degrees
long2meters = lambda degree_resolution: degree_resolution * 100950.05720513177
lat2meters = lambda degree_resolution: degree_resolution * 110772.87259559495


def calculate_resolution(
    ratios, base_resolutions=[0.25, 0.25], print_resolutions=False
):
    r"""Given *ratios* and starting resolutions, calculate level resolutions

    returns a dictionary of resolutions key valued by level"""
    num_levels = len(ratios) + 1

    degree_resolutions = np.empty((num_levels, 2))
    meter_resolutions = np.empty((num_levels, 2))
    degree_resolutions[0, :] = base_resolutions
    meter_resolutions[0, 0] = long2meters(base_resolutions[0])
    meter_resolutions[0, 1] = lat2meters(base_resolutions[1])
    for level in range(1, num_levels):
        degree_resolutions[level, :] = (
            degree_resolutions[level - 1, :] / ratios[level - 1]
        )
        meter_resolutions[level, 0] = long2meters(degree_resolutions[level, 0])
        meter_resolutions[level, 1] = lat2meters(degree_resolutions[level, 1])

    if print_resolutions:
        print("Resolutions:")
        for level in range(num_levels):
            print(
                (
                    " Level %s - (%sº,%sº) - (%s m, %s m)"
                    % (
                        str(level + 1),
                        degree_resolutions[level, 0],
                        degree_resolutions[level, 1],
                        meter_resolutions[level, 0],
                        meter_resolutions[level, 1],
                    )
                )
            )

    resolutions = {}
    for level in range(1, num_levels):
        resolutions[level] = (degree_resolutions, meter_resolutions)
    return [(degree_resolutions, meter_resolutions) for level in range(1, num_levels)]
