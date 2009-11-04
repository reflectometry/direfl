#!/usr/bin/env python

# This program is public domain
#
# Phase inversion author: Norm Berk
# Translated from Mathematica by Paul Kienzle
#
# Phase reconstruction author: Charles Majkrzak
# Converted from Fortran by Paul Kienzle
#
# Reflectivity calculation author: Paul Kienzle
#
# The National Institute of Standards and Technology makes no representations
# concerning this particular software and is not bound in any wy to correct
# possible errors or to provide extensions, upgrades or any form of support.
#
# This disclaimer must accompany any public distribution of this software.
"""
Phase reconstruction and inversion for reflectometry data.

Command line reconstruction + inversion:

    python invert.py -b 2.1 -f 0 -0.53 --thickness=400 f1.refl f2.refl

Command line inversion only:

    python invert.py --thickness=150 wsh02_re.dat

Scripts can use the *reconstruct* and *invert* functions.  For example:

    import invert
    backing = 2.1
    fronting = 0,-0.53
    phase = invert.reconstruct("file1","file2",backing,fronting[1],fronting[2])
    inversion = invert.invert(data=(phase.Q,phase.RealR), thickness=200)
    inversion.plot()
    inversion.save("profile.dat")

The resulting profile has attributes for the input (*Q*, *RealR*) and the
output (*z*, *rho*, *drho*).  There are methods for plotting  (*plot*,
*plotresid*) and storing (*save*).  The analysis can be rerun with
different attributes (*run(key=val,...)*).

See :meth:`SurroundVariation` and :meth:`Inversion` for details.

The algorithm is described in [Berk2009]_ and references therein.
It is based on the partial differential equation solver described
in [Sacks1993].

References
==========

.. [Berk2009] N. F. Berk and C. F. Majkrzak, "Statistical Analysis of
Phase-Inversion Neutron Specular Reflectivity", Langmuir 25, 4132-4144 (2009)

.. [Sacks1993] P. E. Sacks, Wave Motion 18, 21-30 (1993)
"""

from __future__ import division
import numpy
from numpy import pi, inf, nan, sqrt, exp, sin, cos, tan, log
from numpy import ceil, floor, real, imag
from numpy import (interp, diff, sum, mean, std,
                   linspace, array, arange, hstack, zeros, diag)
from numpy.fft import fft
from numpy.random import uniform, poisson, normal

# Common SLDs
silicon = Si = 2.1
sapphire = Al2O3 = 5.0
water = H2O = -0.56
heavywater = D2O = 6.33
lightheavywater = HDO = 2.9 # 50-50 mixture of H2O and D2O

def invert(**kw):
    """
    Invert data returning an :class:`Inversion` object.

    If outfile is specified, save z,rho,drho to the named file.

    If plot=True, show a plot before returning
    """
    doplot = kw.pop('plot',True)
    outfile = kw.pop('outfile',None)
    inverter = Inversion(**kw)
    inverter.run()
    if outfile is not None:
        inverter.save(outfile)
    if doplot:
        import pylab
        inverter.plot()
        pylab.ginput(show_clicks=False)
    return inverter


class Inversion:
    """
    Inversion calculator.

    This object holds the data and results associated with the direct inversion
    of the real value of the phase from a reflected signal.

    The following attributes and methods are of most interest::

        *data*, *thickness*, *surround*  (inputs)
        *z*, *rho*, *drho*               (computed profile)
        *plot*, *save*                   (output methods)
        *stages*, *monitor* , *noise*    (uncertainty controls)

    A number of additional controls are described below for completeness.

    Inputs::

        *data*               input filename or Q,RealR data  (required)
        *thickness* (1000)   film thickness
        *surround* (0)       substrate SLD
        *Qmin* (0)           minimum Q to use from data
        *Qmax* (None)        maximum Q to use from data
        *backrefl* (True)    measures reflection from the back of the sample
        *scalefactor* (1e-6) so SLD can be in human units

    Uncertainty controls::

        *stages* (4)        number of inversions to average over
        *monitor* (50000)   for generating poisson noise
        *noise* (10)        for generating uniform noise

    Uncertainty is handled by averaging over a number of inversions with
    noise added to the input data for each inversion.  The noise is a
    combination of Poisson noise modified by a random uniform scale factor::

        *noise* U[-1,1] (poisson(*monitor* |re r|)/*monitor* - |re r|)

    That is, a value is pulled from the Poisson distribution of the
    expected counts, and the noise is the difference between this and
    the actual counts.  This is further scaled by a fudge factor and
    a further random uniform in [-1,1].

    Inversion controls::

        *iters* (6)         number of iterations to use for inversion
        *rhopoints* (128)   number of steps in the returned profile
        *calcpoints* (4)    number of internal steps per profile step
        *showiters* (False) set to true to show inversion converging
        *ctf_window* (0)    cosine transform smoothing

    Computed profile::

        *Qinput*, *RealRinput*    input data
        *Qmeshed*, *RealRmeshed*  gridded input data used for calculation
        *Q*,*RealR*,*dRealR*      output data
        *z*,*rho*,*drho*          output profile

    The gridding algorithm resamples the data on an even grid using linear
    interpolation.  Values below Qmim and above Qmax are set to zero.  The
    number of points between Qmin and Qmax is preserved.  This works best
    when data are equally spaced to begin with, starting a k*dQ for some k.


    Output methods::

        *save*         save the profile to a file
        *plot*         plot data and profile

    Additional methods::

        *run*          run or rerun the inversion
        *refl*         compute reflectivity from profile
        *plotdata*     plot just the data
        *plotprofile*  plot just the profile
        *plotresid*    plot data minus theory

    Note that the effect of the *surround* has been removed from the
    data in the process of reconstructing the phase.  The reflectivity
    computed from *rho* will not match the input data.  For that you
    need to compute reflectivity from *rho*-*surround*.  This is done
    in :meth:`plotresid` which shows the difference between measured
    and inverted reflectivity.

    You may need to scale the computed Q values by a small factor
    (e.g., 1.02) for the computed reflectivity to match the data.
    For unclear reasons a q-contraction sets in, probably due to
    binning in the inversion.  You can also try scaling z by a
    small factor.  This problem is reduced by having a larger
    number of profile steps, such as *calcpoints*=4

    Set *ctf_window* to a small non-zero value in order to smooth
    the cosine transform step in the inversion.
    """
    Qmin = 0
    Qmax = None
    thickness = 1000
    scalefactor = 1e-6
    rhopoints = 128
    calcpoints = 4
    monitor = 50000
    noise = 10
    surround = 0
    ctf_window = 0
    stages = 10
    iters = 6
    showiters = False
    backrefl = True

    def __init__(self, data=None, **kw):
        # Load the data
        if isinstance(data, basestring):
            self._loaddata(data)
        else: # assume it is a pair, e.g., a tuple, a list, or an Nx2 array.
            Q,RealR = data
            self._setdata(Q,RealR)

        # Run with current keywords
        self._set(**kw)

    def _loaddata(self, file):
        """
        Load data from a file of q,real(r)
        """
        Q,RealR = numpy.loadtxt(file).T
        self._setdata(Q, RealR, name=file)

    def _setdata(self, Q, RealR, name="data"):
        """
        Set data from q,real(r) vectors.

        Resamples the data on an even grid, setting values below Qmin
        and above Qmax to zero.  The number of points between Qmin and
        Qmax is preserved.  This works best when data are equally spaced
        to begin with, starting a k*dQ for some k.

        *Qinput*, *RealRinput* are set to a copy of the original data.
        *Qmeshed*, *RealRmeshed* are set to the gridded data.
        """
        self.name = name
        # Force equal spacing by interpolation
        Q,RealR = array(Q),array(RealR)
        self.Qinput,self.RealRinput = Q,RealR

        # Trim from Qmin to Qmax
        if self.Qmin != None:
            Q,RealR = Q[Q>=self.Qmin], RealR[Q>=self.Qmin]
        if self.Qmax != None:
            Q,RealR = Q[Q<=self.Qmax], RealR[Q<=self.Qmax]

        # Resample on even spaced grid, preserving approximately the
        # points between Qmin and Qmax
        dQ = (Q[-1]-Q[0])/(len(Q) - 1)
        npts = int(Q[-1]/dQ + 1.5)
        Q,RealR = remesh([Q,RealR], 0, Q[-1], npts, left=0, right=0)
        self.Qmeshed,self.RealRmeshed = Q,RealR

    def run(self, **kw):
        """
        Run multiple inversions with resynthesized data for each.

        All control keywords from the constructor can be used, except
        *data* and *outfile*.

        Sets *signals* to the list of noisy (Q, RealR) signals and
        sets *profiles* to the list of generated (z,rho) profiles.
        """
        self._set(**kw)
        Q,realR = self.Qmeshed,self.RealRmeshed
        Qmax = self.Qmax if self.Qmax else Q[-1]
        npts = len(realR)
        signals = []
        profiles = []
        for i in range(self.stages):
            pnoise = poisson(self.monitor*abs(realR))/self.monitor - abs(realR)
            unoise = uniform(-1,1,npts)
            noisyR = realR + self.noise*unoise*pnoise
            #noisyR = realR + normal(realR,noise*0.01*abs(realR))
            ctf = self._transform(noisyR, Qmax=Qmax,
                                  bse=0.0*self.scalefactor, porder=1)
            qp = self._invert(ctf, iters=self.iters)
            if self.showiters: # Show individual iterations
                import pylab
                hold = False
                for qpi in qp:
                    pylab.plot(qpi[0],qpi[1],hold=hold)
                    hold = True
                pylab.ginput()
            z,rho = remesh(qp[-1],0,self.thickness,self.rhopoints)
            signals.append((Q,noisyR))
            profiles.append((z,rho))
        self.signals, self.profiles = signals, profiles

    # Computed attributes.
    def _get_z(self):
        return self.profiles[0][0]
    def _get_rho(self):
        #rho *= self.scalefactor
        rho = mean([p[1] for p in self.profiles], axis=0) + self.surround
        return rho[::-1] if self.backrefl else rho
    def _get_drho(self):
        drho = std([p[1] for p in self.profiles], axis=0)
        return drho[::-1] if self.backrefl else drho
    def _get_Q(self):
        return self.Qmeshed
    def _get_RealR(self):
        return mean([p[1] for p in self.signals], axis=0)
    def _get_dRealR(self):
        return std([p[1] for p in self.signals], axis=0)
    z = property(_get_z)
    rho = property(_get_rho)
    drho = property(_get_drho)
    Q = property(_get_Q)
    RealR = property(_get_RealR)
    dRealR = property(_get_dRealR)

    def save(self, outfile):
        """
        Save z,rho,drho to three column text file named *outfile*.
        """
        numpy.savetxt(outfile, array([self.z,self.rho,self.drho]).T)

    def refl(self, Q=None, freefilm=False):
        """
        Return the complex reflectivity amplitude.

        Use *Q* if provided, otherwise use the evenly spaced Q values used
        for the inversion.

        If *freefilm* is True, then compute the reflectivity of the
        free standing film, otherwise use the surround variation provided
        on input.
        """
        if Q == None: Q == self.Q
        dz = hstack([diff(self.z),0])
        rho = hstack([0,self.rho,0])
        rho = self.rho if not freefilm else self.rho-self.surround
        r = refl(Q,dz,rho)
        return  r

    def plot(self, details=False, resid=False):
        """
        Plot the data and the inversion.

        If *details* is True, then plot the individual stages used to calculate
        the average, otherwise just plot the envelope.
        """
        import pylab
        pylab.subplot(211 if not resid else 311)
        self.plotdata(details=details)
        pylab.title("Direct inversion of "+self.name)
        if resid:
            pylab.subplot(312)
            self.plotresid(details=details)
        pylab.subplot(212 if not resid else 313)
        self.plotprofile(details=details)

    def plotdata(self, details=False):
        """
        Plot the input data.

        If *details* is True, then plot the individual stages used to calculate
        the average, otherwise just plot the envelope.
        """
        import pylab
        if not hasattr(self, 'signals'):
            pylab.plot(self.Qmeshed, self.Qmeshed**2*self.RealRmeshed)
            return

        Q,RealR,dRealR = self.Q, self.RealR, self.dRealR
        [orig] = pylab.plot(Q, Q**2*RealR)
        r = self.refl(Q, freefilm=True)
        pylab.plot(Q, Q**2*real(r), 'g')
        pylab.legend(['original','inverted'])
        if details:
            Q = self.Q
            hold = pylab.ishold()
            for p in self.signals:
                pylab.plot(Q, Q**2*p[1], hold=hold)
                hold=True
        else:
            pylab.fill_between(Q,Q**2*(RealR-dRealR),Q**2*(RealR+dRealR),
                               color=orig.get_color(),alpha=0.5)
            #pylab.plot(Q, Q**2*(RealR+dRealR), '--', color=h.get_color())
            #pylab.plot(Q, Q**2*(RealR-dRealR), '--', color=h.get_color())
        pylab.ylabel("Q**2 Re r")
        pylab.xlabel("Q (inv A)")

    def plotprofile(self, details=False):
        """
        Plot the computed profiles.

        If *details* is True, then plot the individual stages used to calculate
        the average, otherwise just plot the envelope.
        """
        import pylab
        pylab.grid(True)
        if details:
            hold = pylab.ishold()
            for p in self.profiles:
                pylab.plot(p[0], p[1]+self.surround, hold=hold)
                hold=True
        else:
            z,rho,drho = self.z, self.rho, self.drho
            [h] = pylab.plot(z, rho)
            pylab.fill_between(z,rho-drho,rho+drho,
                               color=h.get_color(),alpha=0.5)
            #pylab.plot(z, rho+drho, '--', color=h.get_color())
            #pylab.plot(z, rho-drho, '--', color=h.get_color())
        pylab.ylabel('SLD (inv A^2)')
        pylab.xlabel('depth (A)')

    def plotresid(self, details=False):
        """
        Plot the residuals for inversion-input.
        """
        import pylab
        Q,RealR = self.Qinput,self.RealRinput
        r = self.refl(Q, freefilm=True)
        pylab.plot(Q, Q**2*(real(r)-RealR))
        pylab.ylabel('residuals [Q**2 * (Re r - input)]')
        pylab.xlabel("Q (inv A)")

    def _set(self, **kw):
        """
        Set a group of attributes.
        """
        for k,v in kw.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise ValueError("No attribute "+k+" in inversion")
        self.rhoscale =  1e6 / (4 * pi * self.thickness**2)

    def _transform(self, realR, Qmax=None, bse=scalefactor, porder=1):
        """
        Returns the cosine transform function used by inversion
        """
        if not 0 <= porder <= 6:
            raise ValueError("porder must be between 0 and 6")
        npts = len(realR)
        dK = 0.5 * Qmax / npts
        kappa = sqrt(bse)
        dx = self.thickness/self.rhopoints
        dim = int(2*pi/(dx*dK))
        ct = real(fft(realR, dim)/sqrt(dim))
        xs = dx*arange(2*self.rhopoints)
        convertfac = 2*dK/pi * sqrt(dim) * self.thickness
        ctdatax = convertfac * ct[:len(xs)] # * rhoscale

        ## PAK <--
        ## Mathematica guarantees that the interpolation function
        ## goes through the points, so Interpolator(xs, ctall)(xs)
        ## is just the same as ctall, and so newctall is just ctdatax.
        #ctall = ctdatax
        #ctif = Interpolation(xs, ctall, InterpolationOrder -> porder)
        #newctall = ctif(xs)\
        ## Furthermore, "ctf[x_] := newctif[x]" is an identity transform
        ## and is not necessary.
        #newctif = Interpolation(xs, newctall, InterpolationOrder -> porder)
        #ctf[x_] := newctif[x]
        # This is the uncorrected Cosine Transform
        #newctf[x_] := ctf[x] - exp(-kappa*x) * ctf[0]
        # This is the boundstate-corrected Cosine Transform
        ## PAK -->

        raw_ctf = Interpolator(xs, ctdatax, porder=porder)
        ctf = lambda x: raw_ctf(x) - exp(-kappa*x) * raw_ctf(0)
        return ctf

    def _invert(self, ctf, iters):
        """
        Perform the inversion.
        """
        dz = 2/(self.calcpoints*self.rhopoints)
        x = arange(0,ceil(2/dz))*dz
        maxm = len(x)
        if maxm%2 == 0: maxm += 1
        mx = int(maxm/2+0.5)
        h = 2/(2*mx-3)
        g = numpy.hstack((ctf(x[:-1]*self.thickness), [0,0,0]))
        q = 2 * diff(g[:-2])/h
        q[-1] = 0
        ut = arange(2*mx-2)*h*self.thickness/2
        if self.ctf_window > 0:
            # Smooth ctf with 3-sample approximation
            du = self.ctf_window*h*self.thickness/2
            qinter = Interpolator(ut,q,porder=1)
            q = (qinter(ut - du) + qinter(ut) + qinter(ut + du))/3
        q = hstack((q,[0]))
        qp = [(ut, -2*q*self.rhoscale)]

        Delta = zeros((mx,2*mx),'d')
        for iter in range(iters):
            for m in range(2,mx):
                n = array(range(m,2*mx-(m+1)))
                Delta[m,n] = (h**2 * q[m-1] * (g[m+n] + Delta[m-1,n])
                        + Delta[m-1,n+1] + Delta[m-1,n-1] - Delta[m-2,n])
            udiag = -g[:2*mx-2:2] - diag(Delta)[:mx-1]
            mup = len(udiag) - 2
            h = 1/mup
            ut = arange(mup)*h*self.thickness
            q = 2 * diff(udiag[:-1])/h
            qp.append((ut, self.rhoscale*q))
            q = hstack((q,[0,0]))
        return qp


class Interpolator:
    """
    Data interpolator.

    Construct an interpolation function from pairs xi,yi.
    """
    def __init__(self, xi, yi, porder=1):
        if len(xi) != len(yi):
            raise ValueError("xi:%d and yi:%d must have the same length"
                             %(len(xi),len(yi)))
        self.xi,self.yi = xi, yi
        self.porder = porder
        if porder != 1:
            raise NotImplementedError("interp does not support order")
    def __call__(self, x):
        return interp(x, self.xi, self.yi)

def phase_shift(q,r,shift=0):
    return r*exp(1j*shift*q)

def remesh(data, xmin, xmax, npts, left=None, right=None):
    """
    Resample the data on a fixed grid.
    """
    x,y = data
    newx = linspace(xmin, xmax, npts)
    newy = interp(newx, x, y, left=left, right=right)
    return array((newx,newy))


# This program is public domain.
# Author: Paul Kienzle
"""
Optical matrix form of the reflectivity calculation.

O.S. Heavens, Optical Properties of Thin Solid Films
"""
from numpy import isscalar, asarray, zeros, ones, empty
from numpy import exp, sqrt

def refl(Qz,depth,rho,mu=0,wavelength=1,sigma=0):
    """
    Reflectometry as a function of Qz,wavelength.

    Qz (inv angstrom)
        Scattering vector 4*pi*sin(theta)/wavelength. This is an array.
    wavelenth (angstrom)
        Incident wavelength. If present this is a
    rho,mu (uNb)
        scattering length density and absorption of each layer
    depth (angstrom)
        thickness of each layer.  The thickness of the incident medium
        and substrate are ignored.
    sigma (angstrom)
        interfacial roughness.  This is the roughness between a layer
        and the subsequent layer.  There is no interface associated
        with the substrate.  The sigma array should have at least n-1
        entries, though it may have n with the last entry ignored.
    method (parratt | abeles | opticalmatrix)
        method used to compute the reflectivity
    """
    if isscalar(Qz): Qz = array([Qz], 'd')
    n = len(rho)
    nQ = len(Qz)

    # Make everything into arrays
    kz = asarray(Qz,'d')/2
    depth = asarray(depth,'d')
    rho = asarray(rho,'d')
    mu = mu*ones(n,'d') if isscalar(mu) else asarray(mu,'d')
    wavelength = wavelength*ones(nQ,'d') \
        if isscalar(wavelength) else asarray(wavelength,'d')
    sigma = sigma*ones(n-1,'d') if isscalar(sigma) else asarray(sigma,'d')

    # Scale units
    rho *= 1e-6
    mu *= 1e-6

    ## For kz < 0 we need to reverse the order of the layers
    ## Note that the interface array sigma is conceptually one
    ## shorter than rho,mu so when reversing it, start at n-1.
    ## This allows the caller to provide an array of length n
    ## corresponding to rho,mu or of length n-1.
    idx = (kz>=0)
    r = empty(len(kz),'D')
    r[idx] = _refl_calc(kz[idx], wavelength[idx], depth, rho, mu, sigma)
    r[~idx] = _refl_calc(abs(kz[~idx]), wavelength[~idx],
                   depth[-1::-1], rho[-1::-1], mu[-1::-1],
                   sigma[n-2::-1])
    return r


def _refl_calc(kz,wavelength,depth,rho,mu,sigma):
    """Parratt recursion"""
    if len(kz) == 0: return kz

    ## Complex index of refraction is relative to the incident medium.
    ## We can get the same effect using kz_rel^2 = kz^2 + 4*pi*rho_o
    ## in place of kz^2, and ignoring rho_o
    kz_sq = kz**2 + 4*pi*rho[0]
    k = kz

    # According to Heavens, the initial matrix should be [ 1 F; F 1],
    # which we do by setting B=I and M0 to [1 F; F 1].  An extra matrix
    # multiply versus some coding convenience.
    B11 = 1
    B22 = 1
    B21 = 0
    B12 = 0
    for i in xrange(0,len(rho)-1):
        k_next = sqrt(kz_sq - (4*pi*rho[i+1] + 2j*pi*mu[i+1]/wavelength))
        F = (k - k_next) / (k + k_next)
        F *= exp(-2*k*k_next*sigma[i]**2)
        M11 = exp(1j*k*depth[i]) if i>0 else 1
        M22 = exp(-1j*k*depth[i]) if i>0 else 1
        M21 = F*M11
        M12 = F*M22
        C1 = B11*M11 + B21*M12
        C2 = B11*M21 + B21*M22
        B11 = C1
        B21 = C2
        C1 = B12*M11 + B22*M12
        C2 = B12*M21 + B22*M22
        B12 = C1
        B22 = C2
        k = k_next

    r = B12/B11
    return r

def reconstruct(file1,file2,b,f1,f2):
    return SurroundVariation(file1,file2,b,f1,f2)

class SurroundVariation:
    """
    Phase reconstruction by surround variation.

    Takes two reflectivity signals measured by back reflectivity through
    a substrate and computes the corresponding real and imaginary
    reflectivity.

    Inputs::

        *file1*, *file2*  reflectivity measurements
        *f1*, *f2*  SLD of surrounds for measurements in *file1* and *file2*
        *b*         SLD of he substrate

    Outputs::

        *RealR*, *ImagR*  real and imaginary reflectivity
        *alpha*, *beta*, *tfs*  intermediate values in the calculation
        *name1*, *name2*  names of the input files

    *file1* and *file2* can be pairs of vectors (q1,r1), (q2,r2) or files
    containing at least two columns q,r, with remaining columns such as
    dr, dq, lambda ignored.
    """
    def __init__(self, file1, file2, b, f1, f2):
        self.b = b
        self.f1, self.f2 = f1, f2
        self._load(file1, file2)
        self._calc()

    def _load(self, file1, file2):
        if isinstance(file1, basestring):
            d1 = numpy.loadtxt(file1).T
            name1 = file1
        else:
            d1 = file1
            name1 = "data1"
        if isinstance(file2, basestring):
            d2 = numpy.loadtxt(file2).T
            name2 = file2
        else:
            d2 = file2
            name2 = "data2"
        q1,r1 = d1[0:2]
        q2,r2 = d2[0:2]
        if not q1.shape == q2.shape or not all(q1==q2):
            raise ValueError("Q points do not match in data files")
        self.name1,self.name2 = name1,name2
        self.q, self.r1, self.r2 = q1, r1, r2

    def _calc(self):
        res = _phase_reconstruction(self.q, self.r1, self.r2,
                                    self.b*1e-6, self.f1*1e-6, self.f2*1e-6)
        self.RealR = res['rre']
        self.ImagR = res['rimp']
        self.alpha = res['alpp']
        self.beta = res['betp']
        self.tfs = res['tfs']


def _phase_reconstruction(q, rs1, rs2, GBF, GAF1, GAF2):
    """
    Compute phase reconstruction from back reflectivity on paired samples.

    Inputs::

        *q*  is the measurement positions
        *rs1*, *rs2* are the measurements in the two conditions
        *GBF* is the backing material
        *GAF1*, *GAF2* are the fronting materials corresponding to *rs1*, *rs2*

    Returns a dictionary containing::

        *rre* real signal
        *rimp* +imaginary signal
        *rimm* -imaginary signal
        *alpp* alpha intermediate value
        *betp* beta intermediate value
        *tfs* refractive index for the backing material (??)
    """

    qsq = q*q + 16.*pi*GBF
    RIBFS = 1. - 16.*pi*GBF/qsq
    RIAF1S = 1. - 16.*pi*GAF1/qsq
    RIAF2S = 1. - 16.*pi*GAF2/qsq
    RIBF = sqrt(RIBFS)
    RIAF1 = sqrt(RIAF1S)
    RIAF2 = sqrt(RIAF2S)
    sum1 = 2.*((1.+rs1)/(1.-rs1))*RIAF1*RIBF
    sum2 = 2.*((1.+rs2)/(1.-rs2))*RIAF2*RIBF
    alpp = (sum1-sum2)*RIBFS/(RIAF1S-RIAF2S)
    betp = (RIAF2S*sum1-RIAF1S*sum2)/(RIAF2S-RIAF1S)
    rre = (alpp-betp)/(2.*RIBFS+alpp+betp)
    gamps = alpp*betp-RIBFS*RIBFS
    gamp = sqrt(gamps)
    rimp = -2.0*gamp/(2.0*RIBFS+alpp+betp)
    rimm = -rimp
    tfs = 2.0*RIBFS

    return dict(rimp=rimp, rimm=rimm, rre=rre, alpp=alpp, betp=betp, tfs=tfs)


def main():
    import sys
    import os
    from optparse import OptionParser, OptionGroup
    description="""
    Compute the scattering length density profile from the real portion
    of the phase reconstructed reflectivity.  Call with a single two column
    data file for inversion from phase reconstructed data, or with a pair
    of reduced reflectivity datasets for complete phase inversion.  The
    phase inversion case requires two fronting materials and one backing
    material to be specified.
    """
    parser = OptionParser(usage="%prog [options] data",
                          description=description,
                          version="%prog 1.0")

    group = OptionGroup(parser, "Sample description", description=None)
    group.add_option("-t","--thickness",dest="thickness",
                      default=Inversion.thickness,type="float",
                      help="sample thickness (A)")
    group.add_option("-b","--backing",dest="backing",
                      default=Inversion.surround, type="float",
                      help="sample backing material (10^6 * SLD)")
    group.add_option("-f","--fronting",dest="fronting",
                      type="float", nargs=2,
                      help="fronting materials f1 f2 (10^6 * SLD) for phase inversion")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Data description", description=None)
    group.add_option("--qmin",dest="qmin",
                      default=Inversion.Qmin, type="float",
                      help="minimum Q value to use from the data")
    group.add_option("--qmax",dest="qmax",
                      default=Inversion.Qmax, type="float",
                      help="maximum Q value to use from the data")
    group.add_option("-n","--noise",dest="noise",
                      default=Inversion.noise, type="float",
                      help="noise scaling")
    group.add_option("-M","--monitor",dest="monitor",
                      default=Inversion.monitor, type="int",
                      help="monitor counts used for measurement")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Outputs", description=None)
    group.add_option("-o","--outfile",dest="outfile", default=None,
                      help="output file (infile.prf) or - for console output")
    group.add_option("-v","--verbose",dest="doplot",
                      action="store_true",
                      help="show plot of result")
    group.add_option("-q","--quiet",dest="doplot",
                      action="store_false",default=True,
                      help="don't show output plot")
    group.add_option("-r","--resid",dest="resid",
                      action="store_true",default=False,
                      help="show residual plot")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Calculation controls", description=None)
    group.add_option("--zsteps",dest="rhopoints",
                      default=Inversion.rhopoints, type="int",
                      help="number of profile steps [dz = thickness/zsteps]")
    group.add_option("-z","--dz",dest="dz",
                      default=None, type="float",
                      help="max profile step size (A) [zsteps = thickness/dz]")
    group.add_option("--calcsteps",dest="calcpoints",
                      default=Inversion.rhopoints, type="int",
                      help="number of calculation points per profile step")
    group.add_option("-A","--stages",dest="stages",
                      default=Inversion.stages, type="int",
                      help="number of inversions to average over")
    group.add_option("--test",dest="test",
                      action="store_true",default=False,
                      help="run test suite")
    parser.add_option_group(group)


    (options, args) = parser.parse_args()
    if options.test:
        return test(options)

    if len(args) < 1 or len(args) > 2:
         parser.error("need real R data file or pair of reflectivities")

    elif len(args) == 1:
        data = args[0]
    elif len(args) == 2:
        if not options.fronting or not options.backing:
            parser.error("need fronting and backing for phase inversion")
        f1,f2 = options.fronting
        b = options.backing
        phase = SurroundVariation(args[0],args[1],b=b,f1=f1,f2=f2)
        data = phase.Q, phase.RealR

    if options.dz: options.rhopoints = ceil(1/options.dz)
    res = Inversion(data=data,
                    stages=options.stages,
                    rhopoints=options.rhopoints, calcpoints=options.calcpoints,
                    noise=options.noise, monitor=options.monitor,
                    thickness=options.thickness, surround=options.backing)
    res.run(showiters=False)

    if options.outfile == None:
        basefile = os.path.splitext(os.path.basename(infile))[0]
        options.outfile = basefile+os.path.extsep+"prf"
    if options.outfile == "-":
        print "# z  rho  drho"
        for z,rho,drho in zip(res.z, res.rho, res.drho):
            print "%g %g %g"%(z,rho,drho)
    elif options.outfile != None:
        res.save(options.outfile)
    if options.doplot:
        import pylab
        res.plot(resid=options.resid)
        pylab.show()

def _test1(sample, b, f1, f2, q, plot=False):
    if plot: import pylab
    rho = [p[0] for p in reversed(sample)]
    d = [0] + [p[1] for p in reversed(sample)] + [0]
    rf = refl(q,d,[-b]+[p-b for p in reversed(rho)]+[0])
    r1 = refl(q,d,[b]+rho+[f1])
    r2 = refl(q,d,[b]+rho+[f2])
    R1 = abs(r1)**2
    R2 = abs(r2)**2
    if plot:
        pylab.subplot(221)
        pylab.semilogy(q,R1,hold=False)
        pylab.semilogy(q,R2,hold=True)
        pylab.legend(['f1','f2'])
        pylab.title('Measured data')
        pylab.ylabel('R')
    phase = SurroundVariation((q,R1),(q,R2),b=b,f1=f1,f2=f2)
    if plot:
        pylab.subplot(223)
        pylab.plot(q,q**2*phase.RealR,hold=False)
        pylab.plot(q,q**2*real(rf),hold=True)
        pylab.legend(['computed','actual'])
        pylab.xlabel('q')
        pylab.ylabel('q**2 * Re r')
        pylab.title('Phase inversion')
    invert = Inversion((q,phase.RealR),thickness=sum(d)+50)
    invert.run()
    if plot:
        pylab.subplot(222)
        invert.plotdata()
        pylab.subplot(224)
        invert.plotprofile()
        pylab.ginput()

    #assert ((phase.RealR-real(rf))<real(rf)*1e-12).all()

def test(options):
    q = linspace(0,0.3,100)
    sample = ([(5,100),(2,200)])
    b,f1,f2 = 2.1,-0.53, 2.3
    _test1(sample=sample,b=b,f1=f1,f2=f2,q=q,plot=True)


if __name__ == "__main__":
    main()
