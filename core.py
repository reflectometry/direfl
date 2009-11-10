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

# Note: save this file as invert to run as a stand-alone program
"""
Phase reconstruction and inversion for reflectometry data.

Command line phase reconstruction + phase inversion:

    python invert.py -b 2.1 -f 0 -0.53 --thickness=400 f1.refl f2.refl

Command line phase inversion only:

    python invert.py --thickness=150 wsh02_re.dat

Scripts can use :func:`reconstruct` and :func:`invert`.  For example::

    import invert
    substrate = 2.1
    f1, f2 = 0, -0.53
    phase = invert.reconstruct("file1", "file2", substrate, f1, f2)
    inversion = invert.invert(data=(phase.Q,phase.RealR), thickness=200)
    inversion.plot()
    inversion.save("profile.dat")

The resulting profile has attributes for the input (*Q*, *RealR*) and the
output (*z*, *rho*, *drho*).  There are methods for plotting  (*plot*,
*plotresid*) and storing (*save*).  The analysis can be rerun with
different attributes (*run(key=val,...)*).

See :func:`reconstruct` and :class:`Inversion` for details.

The phase reconstruction algorithm is described in [Majkrzak2003].  The
phase inversion algorithm is described in [Berk2009]_ and references therein.
It is based on the partial differential equation solver described
in [Sacks1993]_.

References
==========

.. [Majkrzak2003] C. F. Majkrzak, N. F. Berk and U. A. Perez-Salas,
"Phase-Sensitive Neutron Reflectometry", *Langmuir* 19, 7796-7810 (2003).

.. [Berk2009] N. F. Berk and C. F. Majkrzak, "Statistical analysis of
phase-inversion neutron specular reflectivity", *Langmuir* 25, 4132-4144 (2009)

.. [Sacks1993] P. E. Sacks, *Wave Motion* 18, 21-30 (1993)
"""

from __future__ import division
import numpy
from numpy import pi, inf, nan, sqrt, exp, sin, cos, tan, log
from numpy import ceil, floor, real, imag, sign, isinf, isnan
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

    Inversion converts a real reflectivity amplitude as computed by
    :func:`reconstruct` into a step profile of scattering length density
    as a function of depth.  This process will only work for real-valued
    scattering potentials --- with non-negligible absorption the results
    will be incorrect.  With X-rays, the absorption is too high for this
    technique to be used successfully.  For details on the underlying
    theory, see _[Berk2009].

    The following attributes and methods are of most interest::

        *data*, *thickness*, *substrate*, *Qmin*, *Qmax*  (`Inputs`__)
        *stages*, *monitor*, *noise*     (`Uncertainty controls`__)
        *rhopoints*, *calcpoints*        (`Inversion controls`__)
        *z*, *rho*, *drho*               (`Computed profile`__)
        *plot*, *save*                   (`Output methods`__)

    Inputs
    ======

        *data*               input filename or Q,RealR data  (required)
        *thickness* (400)    film thickness
        *substrate* (0)       substrate SLD
        *Qmin* (0)           minimum Q to use from data
        *Qmax* (None)        maximum Q to use from data
        *backrefl* (True)    reflection measured through the substrate

    *data* is the name of an input file or a pair of vectors (Q,RealR),
    where RealR is the real portion of the complex reflectivity amplitude.

    *thickness* defines the total thickness of the film of interest.  If
    the value chosen is too small, the inverted profile will not be able
    to match the input reflection signal.  If the thickness is too large,
    the film of interest should be properly reconstructed, but will be
    extended into a reconstructed vacuum layer above of the film.  The
    reflection signal from this profile will show excess variation as
    the inversion process adapts to the noise in the input.

    *substrate* is the scattering length density of the substrate.  The
    inversion calculation determines the scattering length densities (SLDs)
    within the profile relative to the SLD of the substrate.  Entering
    the correct value of substrate will shift the profile back to the
    correct values.

    *Qmin*, *Qmax* is the range of input data to use for the calculation.
    Reduce *Qmax* to avoid contamination from noise at high Q and improve
    precision.  However, doing this will reduce the size of the features
    that you are sensitive to in your profile.  Increase *Qmin* to avoid
    values at low Q which will not have the correct phase reconstruction
    when Q is less than Qc^2 for both surround variation measurements
    used in the phase reconstruction calculation. Use this technique
    sparingly --- the overall shape of the profile is sensitive to data
    at low Q.  *Qmax* and *Qmin* default to the limits of the input data.

    TODO: test and debug backrefl
    *backrefl* should be true if the film is measured with an incident
    beam through the substrate rather than the surface.

    Uncertainty controls
    ====================

        *stages* (4)        number of inversions to average over
        *monitor* (50000)   for generating poisson noise
        *noise* (10)        for generating uniform noise

    Uncertainty is handled by averaging over *stages* inversions with
    noise added to the input data for each inversion.  The noise is a
    combination of Poisson noise modified by a random uniform scale factor::

        *noise* U[-1,1] (poisson(*monitor* |re r|)/*monitor* - |re r|)

    That is, a value is pulled from the Poisson distribution of the
    expected counts, and the noise is the difference between this and
    the actual counts.  This is further scaled by a fudge factor of *noise*
    and a further random uniform in [-1,1].

    Inversion controls
    ==================

        *rhopoints* (128)   number of steps in the returned profile
        *calcpoints* (4)    number of internal steps per profile step
        *iters* (6)         number of iterations to use for inversion
        *showiters* (False) set to true to show inversion converging
        *ctf_window* (0)    cosine transform smoothing

    *rhopoints* is the number of steps in the profile.  If this value is
    too low, the profile will be coarse.  If it is too high, the computation
    will take a long time.  The additional smoothness generated by a high
    value of *rhopoints* is illusory --- the information content of the
    profile is limited by the number of Q points which have been measured.
    Set *rhopoints* to (1/*dz*) for a step size near *dz* in the profile.

    *calcpoints* is used internally to improve the accuracy of the
    calculation.  For larger values of *rhopoints*, smaller values of
    *calcpoints* are feasible.

    You may need to scale the computed Q values by a small factor
    (e.g., 1.02) for the computed reflectivity to match the data.
    For unclear reasons a q-contraction sets in, probably due to
    binning in the inversion.  You can also try scaling z by a
    small factor.  This problem is reduced by having a larger
    number of profile steps, which we do by setting the default
    value of *calcpoints* to 4.

    *iters* is the number of steps to use in the differential equation
    solver that is at the heart of the inversion process.  A value of 6
    seems to work well.  You can observe this by setting *showiters* to
    True and looking at the convergence of each stage of the averaging
    calculation.

    *showiters* shows the convergence of the inversion calculation.
    Click the graph to move to the next stage.

    *ctf_window* smoothes the cosine transform at the heart of the
    computation.  In practice, it is set to 0 for no smoothing.

    Computed profile
    ================

        *Qinput*, *RealRinput*    input data
        *Q*,*RealR*,*dRealR*      output data
        *z*,*rho*,*drho*          output profile
        *signals*,*profiles*      individual inversion stages

    The input data *Qinput*, *RealRinput* need to be placed on an even grid
    going from 0 to *Qmax* using linear interpolation.  Values below *Qmin*
    are set to zero, and the number of points between *Qmin* and *Qmax* is
    preserved.  This resampling works best when the input data are equally
    spaced, starting at k*dQ for some k.

    The returned *Q*, *RealR*, *dRealR* are the values averaged over multiple
    stages with added noise.  The plots show this as the range of input
    variation used in approximating the profile variation.

    *z*, *rho*, *drho* define the output profile.

    *z* represents the depth into the profile.  *z* equals *thickness*
    at the substrate.  If the thickness is correct, then *z* will be zero
    at the top of the film, but in practice the *thickness* value provided
    will be larger than the actual film thickness, and a portion of the
    vacuum will be included at the beginning of the profile.

    *rho* is the SLD at depth *z* in units of 10^-6 inv A^2.  It is
    calculated from the average of the inverted profiles from the noisy
    data sets, and includes the correction for the substrate SLD defined by
    *substrate*.  The inverted *rho* will contain artifacts from the abrupt
    cutoff in the signal at *Qmin* and *Qmax*.

    *drho* is the uncertainty in the SLD profile at depth *z*.  It is
    calculated from the standard deviation of the inverted profiles from
    the noisy data sets.  The uncertainty *drho* does not take into
    account the possible variation in the signal above *Qmax*.

    The reflectivity computed from *z*, *rho* will not match the input
    data because the effect of the substrate has been removed in the
    process of reconstructing the phase.  Instead, you will need to
    compute reflectivity from *rho*-*substrate* on the reversed profile.
    This is done in :meth:`refl` when no surround material is selected,
    and can be used to show the difference between measured and inverted
    reflectivity.  You may need to increase *calcpoints* or modify
    *thickness* to get a close match.

    *signals* is a list of the noisy (Q,RealR) input signals generated
    by the uncertainty controls, and *profiles* is a list of the
    corresponding (z,rho) profiles.  The first stage is computed without
    noise, so *signals[0]* contains the meshed input and *profiles[0]*
    contains the output of the inversion process without additional noise.

    Output methods
    ==============

    The primary output methods are::

        *save*         save the profile to a file
        *show*         show the profile on the screen
        *plot*         plot data and profile
        *refl*         compute reflectivity from profile
        *run*          run or rerun the inversion with new settings

    Additional methods for finer control of plots::

        *plotdata*     plot just the data
        *plotprofile*  plot just the profile
        *plotresid*    plot data minus theory
    """

    Qmin = 0
    Qmax = None
    thickness = 400
    rhopoints = 128
    calcpoints = 4
    monitor = 50000
    noise = 10
    substrate = 0
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
        Set *Qinput*, *RealRinput* from q,real(r) vectors.
        """
        self.name = name
        # Force equal spacing by interpolation
        Q,RealR = array(Q),array(RealR)
        self.Qinput,self.RealRinput = Q,RealR

    def _remesh(self):
        """
        Returns Qmeshed, RealRmeshed.

        Resamples the data on an even grid, setting values below Qmin
        and above Qmax to zero.  The number of points between Qmin and
        Qmax is preserved.  This works best when data are equally spaced
        to begin with, starting a k*dQ for some k.
        """
        Q, RealR = self.Qinput, self.RealRinput
        # Trim from Qmin to Qmax
        if self.Qmin is not None:
            Q,RealR = Q[Q>=self.Qmin], RealR[Q>=self.Qmin]
        if self.Qmax is not None:
            Q,RealR = Q[Q<=self.Qmax], RealR[Q<=self.Qmax]

        # Resample on even spaced grid, preserving approximately the
        # points between Qmin and Qmax
        dQ = (Q[-1]-Q[0])/(len(Q) - 1)
        npts = int(Q[-1]/dQ + 1.5)
        Q,RealR = remesh([Q,RealR], 0, Q[-1], npts, left=0, right=0)

        return Q,RealR

    def run(self, **kw):
        """
        Run multiple inversions with resynthesized data for each.

        All control keywords from the constructor can be used, except
        *data* and *outfile*.

        Sets *signals* to the list of noisy (Q, RealR) signals and
        sets *profiles* to the list of generated (z,rho) profiles.
        """
        self._set(**kw)
        Q,RealR = self._remesh()
        signals = []
        profiles = []
        for i in range(self.stages):
            if i == 0:
                noisyR = RealR
            else:
                pnoise = poisson(self.monitor*abs(RealR))/self.monitor - abs(RealR)
                unoise = uniform(-1,1,RealR.shape)
                noisyR = RealR + self.noise*unoise*pnoise
            #noisyR = RealR + normal(RealR,noise*0.01*abs(RealR))
            ctf = self._transform(noisyR, Qmax=Q[-1], bse=0, porder=1)
            qp = self._invert(ctf, iters=self.iters)
            if self.showiters: # Show individual iterations
                import pylab
                hold = False
                for qpi in qp:
                    pylab.plot(qpi[0],qpi[1],hold=hold)
                    hold = True
                pylab.ginput(show_clicks=False)
            z,rho = remesh(qp[-1],0,self.thickness,self.rhopoints)
            signals.append((Q,noisyR))
            profiles.append((z,rho))
        self.signals, self.profiles = signals, profiles
        
    def chisq(self):
        """
        Return chisq computed from non-zero dRealR.
        """
        q,rer,drer = self.Q,self.RealR,self.dRealR
        idx = drer > 0
        rerinv = real(self.refl(q[idx]))
        chisq = sum(((rerinv-rer[idx])/drer[idx])**2)/len(q[idx])
        return chisq

    # Computed attributes.
    def _get_z(self):
        return self.profiles[0][0]
    def _get_rho(self):
        """returns SLD profile in 10^-6 * inv A^2 units, with 0 at the top"""
        rho = mean([p[1] for p in self.profiles], axis=0) + self.substrate
        return rho[::-1] if self.backrefl else rho
    def _get_drho(self):
        drho = std([p[1] for p in self.profiles], axis=0)
        return drho[::-1] if self.backrefl else drho
    def _get_Q(self):
        return self.signals[0][0]
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

    def show(self):
        """
        Print z,rho,drho to the screen
        """
        print "# %9s %11s %11s"%("z","rho","drho")
        for point in zip(self.z, self.rho, self.drho):
            print "%11.4f %11.4f %11.4f"%point

    def save(self, outfile=None):
        """
        Save z,rho,drho to three column text file named *outfile*.  If
        *outfile* is not provided, the name of the input file will be
        used, but with the extension replaced by '.amp'.
        """
        if outfile is None:
            basefile = os.path.splitext(os.path.basename(self.name))[0]
            outfile = basefile+os.extsep+"amp"
        fid = open(outfile,"w")
        fid.write("# %13s %15s %15s\n"%("z","rho","drho"))
        numpy.savetxt(fid, array([self.z,self.rho,self.drho]).T)
        fid.close()

    def refl(self, Q=None, surround=None):
        """
        Return the complex reflectivity amplitude.

        Use *Q* if provided, otherwise use the evenly spaced Q values used
        for the inversion.

        If *surround* is provided, compute the reflectivity for the
        free film in the context of the substrate and the surround, otherwise
        compute the reflectivity of the reversed free film to match against
        the real portion of the reflectivity amplitude supplied as input.
        """
        if Q is None: Q == self.Q
        if surround is None:
            dz = hstack((0,diff(self.z)))
            rho = self.rho[::-1]-self.substrate
        else:
            dz = hstack((0,diff(self.z[::-1]),0))
            rho = hstack((surround,self.rho,self.substrate))
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

    def plotdata(self, details=False, lowQ_inset=True):
        """
        Plot the input data.

        If *details* is True, then plot the individual stages used to calculate
        the average, otherwise just plot the envelope.

        If *lowQ_inset* is True, then plot a graph of the low Q values not
        scaled by Q**2.
        """
        import pylab

        if details:
            realplot(self.Qinput, self.RealRinput)
            for p in self.signals:
                realplot(self.Q, p[1], hold=True)
        else:
            realplot(self.Q, self.RealR, dRealR=self.dRealR, label=None,
                     linestyle='', color="blue")
            realplot(self.Qinput, self.RealRinput, label="original",
                     color="blue")
            Rinverted = real(self.refl(self.Qinput))
            realplot(self.Qinput, Rinverted, label="inverted", color="red")
            pylab.legend()

            if lowQ_inset==True:
                # Low Q inset
                orig = pylab.gca()
                box = orig.get_position()
                ax = pylab.axes([box.xmin+0.02, box.ymin+0.02,
                                 box.width/4, box.height/4],
                                 axisbg=[0.95,0.95,0.65,0.85])
                ax.plot(self.Qinput, self.RealRinput, color="blue")
                ax.plot(self.Qinput, Rinverted, color="red")
                ax.text(0.99,0.01,"Q,Re r for Q<0.05",
                        fontsize="10",transform=ax.transAxes,
                        ha='right', va='bottom')
                xmax = 0.05
                ymax = max(max(self.RealRinput[self.Qinput<xmax]),
                           max(Rinverted[self.Qinput<xmax]))
                pylab.setp(ax, xticks=[], yticks=[],
                           xlim=[0,xmax], ylim=[-1,1.1*(ymax+1)-1])
                pylab.axes(orig)


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
                pylab.plot(p[0], p[1]+self.substrate, hold=hold)
                hold=True
        else:
            z,rho,drho = self.z, self.rho, self.drho
            [h] = pylab.plot(z, rho)
            pylab.fill_between(z,rho-drho,rho+drho,
                               color=h.get_color(),alpha=0.3)
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
        r = self.refl(Q)
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

    def _transform(self, RealR, Qmax=None, bse=0, porder=1):
        """
        Returns the cosine transform function used by inversion

        *bse* is bound-state energy, with units of 10^-6 inv A^2.  It
        was used in the past to handle profiles with negative SLD at
        the beginning, but the the plain correction of bse=0 has since
        been found to be good enough for the profiles we are looking at.
        *porder* is the order of the interpolating polynomial, which
        must be 1 for the current interpolation class.
        """
        if not 0 <= porder <= 6:
            raise ValueError("porder must be between 0 and 6")
        npts = len(RealR)
        dK = 0.5 * Qmax / npts
        kappa = sqrt(bse*1e-6)
        dx = self.thickness/self.rhopoints
        xs = dx*arange(2*self.rhopoints)
        dim = int(2*pi/(dx*dK))
        if dim < len(xs):
            raise ValueError("Q spacing is too low for the given thickness")
        # 1/sqrt(dim) is the normalization convention for Mathematica FFT
        ct = real(fft(RealR, dim)/sqrt(dim))
        convertfac = 2*dK/pi * sqrt(dim) * self.thickness
        ctdatax = convertfac * ct[:len(xs)] # * rhoscale

        ## PAK <--
        ## Mathematica guarantees that the interpolation function
        ## goes through the points, so Interpolator(xs, ctall)(xs)
        ## is just the same as ctall, and so newctall is just ctdatax.
        ## Furthermore, "ctf[x_] := newctif[x]" is an identity transform
        ## and is not necessary.  In the end, we only need one
        ## interplotor plus the correction for ctf[0] == 0.
        #ctall = ctdatax
        #ctif = Interpolation(xs, ctall, InterpolationOrder -> porder)
        #newctall = ctif(xs)
        #newctif = Interpolation(xs, newctall, InterpolationOrder -> porder)
        #ctf[x_] := newctif[x]
        # This is the uncorrected Cosine Transform
        #newctf[x_] := ctf[x] - exp(-kappa*x) * ctf[0]
        # This is the boundstate-corrected Cosine Transform
        ## PAK -->

        # This is the uncorrected Cosine Transform
        raw_ctf = Interpolator(xs, ctdatax, porder=porder)
        # This is the boundstate-corrected Cosine Transform
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
        g = numpy.hstack((ctf(x[:-1]*self.thickness), 0,0,0))
        q = 2 * diff(g[:-2])/h
        q[-1] = 0
        ut = arange(2*mx-2)*h*self.thickness/2
        if self.ctf_window > 0:
            # Smooth ctf with 3-sample approximation
            du = self.ctf_window*h*self.thickness/2
            qinter = Interpolator(ut,q,porder=1)
            q = (qinter(ut - du) + qinter(ut) + qinter(ut + du))/3
        q = hstack((q,0))
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
            q = hstack((q,0,0))
        return qp

def realplot(Q, RealR, dRealR=None, scaled=True, **kw):
    """
    Plot Q,Re(r) data.
    """
    import pylab
    scale = 1e6*Q**2 if scaled else 1
    [h] = pylab.plot(Q, scale*RealR,**kw)
    if dRealR is not None:
        pylab.fill_between(Q,scale*(RealR-dRealR),scale*(RealR+dRealR),
                           color=h.get_color(),alpha=0.3)
        #pylab.plot(Q, scale*(R-dR), '--', color=h.get_color())
        #pylab.plot(Q, scale*(R+dR), '--', color=h.get_color())

    pylab.ylabel("10^6 Q**2 Re r" if scaled else "Re r")
    pylab.xlabel("Q (inv A)")

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
    x,y = x[~(isnan(x)|isinf(x))], y[~(isnan(x)|isinf(x))]
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

def reconstruct(file1,file2,u,v1,v2,stages=100):
    """
    Phase reconstruction by surround variation magic.

    Two reflectivity measurements of a film with different surrounding
    media |r_1|^2 and |r_2|^2 can be combined to compute the expected
    complex reflection amplitude r_reversed of the free standing film
    measured from the opposite side.  The calculation can be done by
    varying the fronting media or by varying the backing media.  For
    this code we only support measurements through a uniform substrate *u*,
    on two varying surrounding materials *v1*, *v2*.

    We have to be careful about terminology.  We will use the term
    substrate to mean the base on which we deposit our film of interest,
    and surround to be the material we put on the other side.  We are
    using u for the uniform substrate and v for the varying surround.

    In the experimental setup at the NCNR, we have a liquid resevoir which
    we can place above the film.  We measure first with one liquid in the
    resevoir such as water and again with a contrasting liquid such as
    heavy water (D2O).  We measure the film through the substrate (either
    silicon or sapphire) since they are more transparent to neutrons
    than water.

    .. figure:: backrefl_setup.png
       :alt: experimental setup for back reflectivity

       The incident beam is measured through the substrate, and thus
       subject to the same absorption as the reflected beam.
       Refraction on entering and leaving the substrated is accounted
       for by a small adjustment to Q inside the reflectivity calculation.

    When measuring reflectivity through the substrate, the beam enters
    the substrate from the side, refracts a little because of the steep
    angle of entry, reflects off the sample, and leaves through the other
    side of the substrate with an equal but opposite refraction.  The
    reflectivity calculation takes this into account.  Traveling
    through several centimeters of substrate, some of the beam will
    get absorbed.  We account for this either by entering an incident
    medium transmission coefficient in the reduction process, or by
    measuring the incident beam through the substrate so that it is
    subject to approximately the same absorption.

    The phase cannot be properly computed for Q values which are below
    the critical edge Qc^2 for both surround variations.  This problem
    can be avoided by choosing a substrate which is smaller than the surround
    on at least one of the measurements.  This measurement will not
    have a critical edge at positive Q.  In order to do a correct
    footprint correction the other measurement should use a substrate SLD
    greater than the surround SLD.

    If the input file records uncertainty in the measurement, we
    perform a Monte Carlo uncertainty estimate of the reconstructed
    complex amplitude.

    Inputs::

        *file1*, *file2*  reflectivity measurements at identical Q values
        *v1*, *v2*  SLD of varying surrounds in *file1* and *file2*
        *u*         SLD of the uniform substrate
        *stages*    number of trials in Monte Carlo uncertainty estimate

    Returns a :class:`SurroundVariation` object with the following
    attributes::

        *RealR*, *ImagR*     real and imaginary reflectivity
        *dRealR*, *dImagR*   Monte Carlo uncertainty estimate
        *name1*, *name2*     names of the input files
        *save(file)*         save Q, RealR, ImagR to a file
        *show()*, *plot()*   display the results

    *file1* and *file2* can be pairs of vectors (q1,r1), (q2,r2) or files
    containing at least two columns q,r, with remaining columns such as
    dr, dq, lambda ignored.  If a third vector, dr, is present in both
    datasets, then an uncertainty estimate will be calculated for the
    reconstructed phase.
    """
    print "reconstructing"
    return SurroundVariation(file1,file2,u,v1,v2,stages=stages)

class SurroundVariation:
    """
    Surround variation calculation.

    See :func:`reconstruction` for details.

    Attributes::

        *Q*, *RealR*, *ImagR*  real and imaginary reflectivity
        *dRealR*, *dImagR*     Monte Carlo uncertainty estimate or None
        *Qin*, *R1*, *R2*      input data
        *dR1*, *dR2*           input uncertainty or None
        *name1*, *name2*       input file names
        *save(file)*           save output
        *show()*,*plot()*      show Q, RealR, ImagR

    """
    def __init__(self, file1, file2, u, v1, v2, stages=100):
        self.u = u
        self.v1, self.v2 = v1, v2
        self._load(file1, file2)
        self._calc()
        self._calc_err(stages=stages)
        self.clean()

    def clean(self):
        """
        Remove points which are NaN or Inf from the computed phase.
        """
        # Toss invalid values
        Q,re,im = self.Qin,self.RealR,self.ImagR
        if self.dRealR is not None:
            dre,dim = self.dRealR,self.dImagR
            keep = ~reduce(lambda y,x: isinf(x)|isnan(x)|y,
                           [re,im], False)
            self.Q,self.RealR,self.dRealR,self.ImagR,self.dImagR \
                = [v[keep] for v in (Q,re,dre,im,dim)]
        else:
            keep = ~reduce(lambda y,x: isinf(x)|isnan(x)|y,
                           [re,im], False)
            self.Q,self.RealR,self.ImagR \
                = [v[keep] for v in (Q,re,im)]

    def save(self, outfile=None, uncertainty=True):
        """
        Save Q,RealR,ImagR to three column text file named *outfile*.
        Include dRealR,dImagR if they exist and if *uncertainty* is True,
        making a five column file.
        """
        if outfile is None:
            basefile = os.path.splitext(os.path.basename(self.name1))[0]
            outfile = basefile+os.extsep+"amp"

        header = "# %13s %15s %15s"%("Q","RealR","ImagR")
        v = [self.Q, self.RealR, self.ImagR]
        if self.dRealR is not None and uncertainty:
            header += " %15s %15s"%("dRealR","dImagR")
            v += [self.dRealR,self.dImagR]

        fid = open(outfile,"w")
        fid.write(header+"\n")
        numpy.savetxt(fid, array(v).T)
        fid.close()

    def show(self):
        """
        Print Q,RealR, ImagR to the screen
        """
        print "# %9s %11s %11s"%("Q","RealR","ImagR")
        for point in zip(self.Q, self.RealR, self.ImagR):
            print "%11.4g %11.4g %11.4g"%point

    def plot(self):
        import pylab
        realplot(self.Q, self.RealR, dRealR=self.dRealR, label="Re r")
        realplot(self.Q, self.ImagR, dRealR=self.dImagR, label="Im r")
        pylab.legend()

    def _load(self, file1, file2):
        """
        Load the data from files or from tuples of (Q,R).
        """
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
        # Check if we have uncertainty
        try:
            dr1,dr2 = d1[2],d2[2]
        except:
            dr1 = dr2 = None
        if not q1.shape == q2.shape or not all(q1==q2):
            raise ValueError("Q points do not match in data files")
        self.name1,self.name2 = name1,name2
        self.Qin, self.R1in, self.R2in = q1, r1, r2
        self.dR1in, self.dR2in = dr1, dr2

    def _calc(self):
        """
        Call the phase reconstruction calculator.
        """
        re,im = _phase_reconstruction(self.Qin, self.R1in, self.R2in,
                                      self.u, self.v1, self.v2)
        self.RealR, self.ImagR = re,im
        self.Q = self.Qin

    def _calc_err(self, stages):
        if self.dR1in is None:
            dRealR = dImagR = None
        else:
            runs = []
            for i in range(stages):
                R1 = normal(self.R1in,self.dR1in)
                R2 = normal(self.R2in,self.dR2in)
                RealR,ImagR = _phase_reconstruction(self.Qin, R1, R2,
                                                    self.u, self.v1, self.v2)
                runs.append((RealR,ImagR))
            dRealR = std([r[0] for r in runs],axis=0)
            dImagR = std([r[1] for r in runs],axis=0)
        self.dRealR, self.dImagR = dRealR, dImagR


def _phase_reconstruction(Q, R1sq, R2sq, rho_u, rho_v1, rho_v2):
    """
    Compute phase reconstruction from back reflectivity on paired samples
    with varying surface materials.

    Inputs::

        *Q*  is the measurement positions
        *R1sq*, *R2sq* are the measurements in the two conditions
        *rho_v1*, *rho_v2* are the backing media SLDs for *R1sq* and *R2sq*
        *rho_u* is the fronting medium SLD

    Returns RealR, ImagR
    """

    Qsq = Q**2 + 16.*pi*rho_u*1e-6
    usq,v1sq,v2sq = [(1-16*pi*rho*1e-6/Qsq) for rho in (rho_u,rho_v1,rho_v2)]

    sigma1 = 2 * sqrt(v1sq*usq) * (1+R1sq) / (1-R1sq)
    sigma2 = 2 * sqrt(v2sq*usq) * (1+R2sq) / (1-R2sq)

    alpha = usq * (sigma1-sigma2) / (v1sq-v2sq)
    beta = (v2sq*sigma1-v1sq*sigma2) / (v2sq-v1sq)
    gamma = sqrt(alpha*beta - usq**2)
    Rre = (alpha-beta) / (2*usq+alpha+beta)
    Rim = -2*gamma / (2*usq+alpha+beta)

    return Rre,Rim


def main():
    """
    Drive phase reconstruction and direct inversion from the command line.
    """
    import sys
    import os
    from optparse import OptionParser, OptionGroup
    description="""\
Compute the scattering length density profile from the real portion
of the phase reconstructed reflectivity.  Call with a phase reconstructed
reflectivity dataset AMP, or with a pair of reduced reflectivity
datasets RF1 and RF2 for complete phase inversion.   Phase inversion
requires two surrounding materials and one substrate material to be specified.
The measurement is assumed to come through the substrate."""
    parser = OptionParser(usage="%prog [options] AMP or RF1 RF2",
                          description=description,
                          version="%prog 1.0")
    inversion_keys = [] # Collect the keywords we are using

    group = OptionGroup(parser, "Sample description", description=None)
    group.add_option("-t","--thickness",dest="thickness",
                      default=Inversion.thickness,type="float",
                      help="sample thickness (A)")
    group.add_option("-u","--substrate",dest="substrate",
                      default=Inversion.substrate, type="float",
                      help="sample substrate material (10^6 * SLD)")
    group.add_option("-v","--surround",dest="surround",
                      type="float", nargs=2,
                      help="varying materials v1 v2 (10^6 * SLD) [for phase]")
    # fronting is not an inversion key
    inversion_keys += ['thickness','substrate']
    parser.add_option_group(group)

    group = OptionGroup(parser, "Data description", description=None)
    group.add_option("--Qmin",dest="Qmin",
                      default=Inversion.Qmin, type="float",
                      help="minimum Q value to use from the data")
    group.add_option("--Qmax",dest="Qmax",
                      default=Inversion.Qmax, type="float",
                      help="maximum Q value to use from the data")
    group.add_option("-n","--noise",dest="noise",
                      default=Inversion.noise, type="float",
                      help="noise scaling")
    group.add_option("-M","--monitor",dest="monitor",
                      default=Inversion.monitor, type="int",
                      help="monitor counts used for measurement")
    inversion_keys += ['Qmin','Qmax','noise','monitor']
    parser.add_option_group(group)

    group = OptionGroup(parser, "Outputs", description=None)
    group.add_option("-o","--outfile",dest="outfile", default=None,
                      help="profile file (infile.prf), use '-' for console")
    group.add_option("--ampfile",dest="ampfile", default=None,
                      help="amplitude file (infile.amp)")
    group.add_option("-p","--plot",dest="doplot",
                      action="store_true",
                      help="show plot of result")
    group.add_option("-q","--quiet",dest="doplot",
                      action="store_false",default=True,
                      help="don't show output plot")
    group.add_option("-r","--resid",dest="resid",
                      action="store_true",default=False,
                      help="show residual plot")
    # doplot and resid are post inversion options
    parser.add_option_group(group)

    group = OptionGroup(parser, "Calculation controls", description=None)
    group.add_option("--rhopoints",dest="rhopoints",
                      default=Inversion.rhopoints, type="int",
                      help="number of profile steps [dz=thickness/rhopoints]")
    group.add_option("-z","--dz",dest="dz",
                      default=None, type="float",
                      help="max profile step size (A) [rhopoints=thickness/dz]")
    group.add_option("--calcpoints",dest="calcpoints",
                      default=Inversion.calcpoints, type="int",
                      help="number of calculation points per profile step")
    group.add_option("--stages",dest="stages",
                      default=Inversion.stages, type="int",
                      help="number of inversions to average over")
    group.add_option("-a",dest="amp_only", default=False,
                      action="store_true",
                      help="calculate amplitude and stop")
    inversion_keys += ['rhopoints','calcpoints','stages']
    parser.add_option_group(group)


    (options, args) = parser.parse_args()
    if len(args) < 1 or len(args) > 2:
         parser.error("need real R data file or pair of reflectivities")

    basefile = os.path.splitext(os.path.basename(args[0]))[0]
    if len(args) == 1:
        data = args[0]
    elif len(args) == 2:
        if not options.surround or not options.substrate:
            parser.error("need fronting and backing for phase inversion")
        v1,v2 = options.surround
        u = options.substrate
        phase = SurroundVariation(args[0],args[1],u=u,v1=v1,v2=v2)
        data = phase.Q, phase.RealR
        if options.ampfile:
            phase.save(options.ampfile)
        if options.amp_only and options.doplot:
            import pylab
            phase.plot()
            pylab.show()

    if options.amp_only: return

    if options.dz: options.rhopoints = ceil(1/options.dz)
    # Rather than trying to remember which control parameters I
    # have options for, I update the list of parameters that I
    # allow for each group of parameters, and pull the returned
    # values out below.
    res = Inversion(data=data, **dict((key,getattr(options,key))
                                      for key in inversion_keys))
    res.run(showiters=False)

    if options.outfile == None:
        options.outfile = basefile+os.path.extsep+"prf"
    if options.outfile == "-":
        res.show()
    elif options.outfile != None:
        res.save(options.outfile)
    if options.doplot:
        import pylab
        res.plot(resid=options.resid)
        pylab.show()

if __name__ == "__main__":
    main()
