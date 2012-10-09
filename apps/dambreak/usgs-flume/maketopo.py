"""
maketopo:

make some 'artificial' topo surrounding the flume area.
make an initialization file of the water elevation in the flume hopper

"""

import numpy as np
from pyclaw.geotools import topotools as gt
import pylab
import os


def maketopo():
    """
    output topography for entire domain
    """

    #pad
    outfile = 'FlumeRunoutPad_10cm.tt2'
    xlower = 65.0
    xupper = 180.00
    ylower = -10.0
    yupper = 12.0
    nxpoints = int((xupper-xlower)/0.05) + 1
    nypoints = int((yupper-ylower)/0.05) + 1
    gt.topo2writer(outfile,bed_curve,xlower,xupper,ylower,yupper,nxpoints,nypoints)

    #hill
    outfile = 'FlumeHillside_1m.tt2'
    xlower = -10.0
    xupper = 72.0
    ylower = -10.0
    yupper = 12.0
    nxpoints = int((xupper-xlower)/1.0) + 1
    nypoints = int((yupper-ylower)/1.0) + 1
    gt.topo2writer(outfile,hill,xlower,xupper,ylower,yupper,nxpoints,nypoints)

    #bed
    outfile = 'FlumeHopper_-10.0m_4.4m_1cm.tt2'
    xlower = -11.0
    xupper = 71.6
    ylower = 0.0
    yupper = 2.0
    nxpoints = int((xupper-xlower)/0.01) + 1
    nypoints = int((yupper-ylower)/0.01) + 1
    gt.topo2writer(outfile,bed_curve,xlower,xupper,ylower,yupper,nxpoints,nypoints)

    #wall0
    outfile = 'FlumeWall_-10.0m_4.4m_y0_1cm.tt2'
    xlower = -10.0
    xupper = 71.5
    ylower = -0.5
    yupper = 0.0
    nxpoints = int((xupper-xlower)/0.02) + 1
    nypoints = int((yupper-ylower)/0.02) + 1
    gt.topo2writer(outfile,wall,xlower,xupper,ylower,yupper,nxpoints,nypoints)

    #wall2
    outfile= 'FlumeWall_-10.0m_4.4m_y2_1cm.tt2'
    xlower = -10.0
    xupper = 71.5
    ylower = 2.0
    yupper = 2.5
    nxpoints = int((xupper-xlower)/0.02) + 1
    nypoints = int((yupper-ylower)/0.02) + 1
    gt.topo2writer(outfile,wall,xlower,xupper,ylower,yupper,nxpoints,nypoints)


def makeqinit():
    """
    output initialization files
    """
    #test initial file
    outfile= 'FlumeQinit.tt2'
    xlower = -10.0
    xupper = 0.0
    ylower = 0.0
    yupper = 2.0
    nxpoints = int((xupper-xlower)/0.01) + 1
    nypoints = int((yupper-ylower)/0.01) + 1
    gt.topo2writer(outfile,flume_eta,xlower,xupper,ylower,yupper,nxpoints,nypoints)



def pad(X,Y):

    """
    runout pad
    """

    x0 = 71.60
    z0 = 1.1159
    slope = np.tan(-2.5*np.pi/180.0)
    Z = z0 + slope*(X-x0)

    return Z

def hill(X,Y):
    """
    side of the hill
    """

    x0 = 71.60
    z0 = 1.1159 - 3.0
    slope = np.tan(-31.0*np.pi/180.0)
    Z = z0 + slope*(X-x0) + 0.5*np.cos(X-x0)*np.sin(Y)

    return Z

def bed(X,Y):

    x0 = 4.4
    z0 = 38.8249
    slope = np.tan(-31*np.pi/180.0)
    Z = z0 + slope*(X-x0)

    return Z

def bed_curve(X,Y):

    deg2rad = np.pi/180.0
    R = 10.0
    theta1 = 3.0*deg2rad
    theta2 = 31.0*deg2rad
    x1 = 71.6
    z1 = 1.12124432216

    xc = x1 - R*np.cos(1.5*np.pi - theta1)
    zc = z1 - R*np.sin(1.5*np.pi - theta1)

    x0 = xc + R*np.cos(1.5*np.pi - theta2)
    z0 = zc + R*np.sin(1.5*np.pi - theta2)
    Z=np.zeros(np.shape(X))

    yind =  np.where((Y[:,0]<=20.0)&(Y[:,0]>=-20.0))[0]
    xind = np.where((X[0,:]>x0)&(X[0,:]<x1))[0]

    Z[np.ix_(yind,xind)]= zc - np.sqrt(R**2-(X[np.ix_(yind,xind)]-xc)**2)

    xind = np.where(X[0,:]<=x0)[0]
    Z[np.ix_(yind,xind)] = z0 - np.tan(theta2)*(X[np.ix_(yind,xind)]-x0)

    xind =  np.where(X[0,:]>=x1)[0]
    Z[np.ix_(yind,xind)] = z1 - np.tan(theta1)*(X[np.ix_(yind,xind)]-x1)


    return Z

def wall(X,Y):

    x0 = 71.6
    z0 = 1.13 + 2.0
    slope = np.tan(-31*np.pi/180.0)
    Z = z0 + slope*(X-x0)

    return Z

def flume_eta(X,Y):

    hopperlen = 4.7
    hmax = 1.9
    hoppertop = 3.3
    topangle = 17.0*np.pi/180.0
    flumeangle = 31.0*np.pi/180.0
    backangle = (90.0-flumeangle)*np.pi/180.0

    x0 = 0.0
    x1 = (x0-hopperlen)*np.cos(flumeangle)
    yind =  np.where((Y[:,0]<=2.0)&(Y[:,0]>=0.0))[0]
    x1ind = np.where(X[0,:]>=x1)[0]
    x2ind = np.where(X[0,:]<x1)[0]

    Z=np.zeros(np.shape(X))
    elev = bed_curve(x0*np.ones(np.shape(X)),0.0*np.ones(np.shape(Y)))
    Z[np.ix_(yind,x1ind)] = hmax + (x0-X[np.ix_(yind,x1ind)])*np.sin(topangle) + elev[0,0]

    elev = bed_curve(x0*np.ones(np.shape(X)),0.0*np.ones(np.shape(Y)))
    etax1 = hmax + (x0-x1)*np.sin(topangle) + elev[0,0]

    Z[np.ix_(yind,x2ind)] = etax1 - (x1-X[np.ix_(yind,x2ind)])*np.sin(backangle)

    return Z

if __name__=='__main__':
    maketopo()
    makeqinit()

