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

# Note: save this file as invert to run as a stand-alone program.

"""
Core classes and functions:

* :class:`Interpolator`
   Class that performs data interpolation.

* :class:`Inversion`
   Class that implements the inversion calculator.

* :class:`SurroundVariation`
   Class that performs the surround variation calculation.

* :func:`refl`
   Reflectometry as a function of Qz and wavelength.

* :func:`reconstruct`
   Phase reconstruction by surround variation magic.

* :func:`valid_f`
   Calculate vector function using only the finite elements of the array.


Command line phase reconstruction phase inversion::

    invert -u 2.07 -v 6.33 0 --Qmin 0.014 --thickness 1000 qrd1.refl qrd2.refl


Command line phase + inversion only::

    invert --thickness=150 --Qmax 0.35 wsh02_re.dat


Scripts can use :func:`reconstruct` and :func:`invert`.  For example:

.. doctest::

    >>> from direfl.invert import reconstruct, invert
    >>> substrate = 2.07
    >>> f1, f2 = 0, -0.53
    >>> phase = reconstruct("file1", "file2", substrate, f1, f2)
    >>> inversion = invert(data=(phase.Q, phase.RealR), thickness=200)
    >>> inversion.plot()
    >>> inversion.save("profile.dat")

The resulting profile has attributes for the input (*Q*, *RealR*) and the
output (*z*, *rho*, *drho*).  There are methods for plotting  (*plot*,
*plot_residual*) and storing (*save*).  The analysis can be rerun with
different attributes (*run(key=val, ...)*).

See :func:`reconstruct` and :class:`Inversion` for details.

The phase reconstruction algorithm is described in [Majkrzak2003]_.  The
phase inversion algorithm is described in [Berk2009]_ and references therein.
It is based on the partial differential equation solver described
in [Sacks1993]_.

References
==========

.. [Majkrzak2003] C. F. Majkrzak, N. F. Berk and U. A. Perez-Salas,
   "Phase-Sensitive Neutron Reflectometry", *Langmuir* 19, 7796-7810 (2003).

.. [Berk2009]     N. F. Berk and C. F. Majkrzak, "Statistical analysis of
   phase-inversion neutron specular reflectivity", *Langmuir* 25, 4132-4144 (2009).

.. [Sacks1993]    P.E. Sacks, *Wave Motion* 18, 21-30 (1993).
"""
from __future__ import division, print_function
import os
from functools import reduce

import numpy as np
from numpy import (
    pi, inf, nan, sqrt, exp, sin, cos, tan, log,
    ceil, floor, real, imag, sign, isinf, isnan, isfinite,
    diff, mean, std, arange, diag, isscalar)
from numpy.fft import fft

# The following line is temporarily commented out because Sphinx on Windows
# tries to document the three modules as part of inversion.api.invert when it
# should be skipping over them.  The problem may be caused by numpy shipping
# these modules in a dll (mtrand.pyd) instead of in .pyc or .pyo files.
# Furthermore, Sphinx 1.0 generates non-fatal error messages when processing
# these imports and Sphinx 0.6.7 generates fatal errors and will not create the
# documentation.  Sphinx on Linux does not exhibit these problems.  The
# workaround is to use implicit imports in the functions or methods that use
# these functions.
#from numpy.random import uniform, poisson, normal

from .calc import convolve
from .util import isstr

# Custom colors
DARK_RED = "#990000"

# Common SLDs
silicon = Si = 2.07
sapphire = Al2O3 = 5.0
water = H2O = -0.56
heavywater = D2O = 6.33
lightheavywater = HDO = 2.9 # 50-50 mixture of H2O and D2O

def invert(**kw):
    """
    Invert data returning an :class:`Inversion` object.

    If outfile is specified, save z, rho, drho to the named file.
    If plot=True, show a plot before returning
    """

    doplot = kw.pop('plot', True)
    outfile = kw.pop('outfile', None)
    inverter = Inversion(**kw)
    inverter.run()
    if outfile is not None:
        inverter.save(outfile)
    if doplot:
        import pylab
        inverter.plot()
        pylab.ginput(show_clicks=False)
    return inverter


class Inversion():
    """
    Class that implements the inversion calculator.

    This object holds the data and results associated with the direct inversion
    of the real value of the phase from a reflected signal.

    Inversion converts a real reflectivity amplitude as computed by
    :func:`reconstruct` into a step profile of scattering length density
    as a function of depth.  This process will only work for real-valued
    scattering potentials - with non-negligible absorption the results
    will be incorrect. With X-rays, the absorption is too high for this
    technique to be used successfully. For details on the underlying
    theory, see [Berk2009]_.

    The following attributes and methods are of most interest:

    **Inputs:**

      =================   =========================================================
      Input Parameters    Description
      =================   =========================================================
      *data*              The name of an input file or a pair of vectors (Q, RealR)
                          where RealR is the real portion of the complex
                          reflectivity amplitude.input filename or Q, RealR data
                          (required).
      *thickness* (400)   Defines the total thickness of the film of interest. If
                          the value chosen is too small, the inverted profile will
                          not be able to match the input reflection signal.  If
                          the thickness is too large, the film of interest should
                          be properly reconstructed, but will be extended into a
                          reconstructed substrate below the film.film thickness.
      *substrate* (0)     It is the scattering length density of the substrate. The
                          inversion calculation determines the scattering length
                          densities (SLDs) within the profile relative to the SLD
                          of the substrate. Entering the correct value of
                          substrate will shift the profile back to the correct
                          values.
      *bse* (0)           It is the bound state energy correction factor.  Films
                          with large negative potentials at their base sometimes
                          produce an incorrect inversion, as indicated by an
                          incorrect value for the substrate portion of a film. A
                          value of substrate SLD - bound state SLD seems to correct
                          the reconstruction.
      *Qmin* (0)          Minimum Q to use from data. Reduce *Qmax* to avoid
                          contamination from noise at high Q and improve precision.
                          However, doing this will reduce the size of the features
                          that you are sensitive to in your profile.
      *Qmax* (None)       Maximum Q to use from data. Increase *Qmin* to avoid
                          values at low Q which will not have the correct phase
                          reconstruction when Q is less than Qc^2 for both surround
                          variation measurements used in the phase reconstruction
                          calculation. Use this technique sparingly --- the overall
                          shape of the profile is sensitive to data at low Q.
      *backrefl* (True)   Reflection measured through the substrate. It is True if
                          the film is measured with an incident beam through the
                          substrate rather than the surface.
      =================   =========================================================

    **Uncertainty controls:**

      Uncertainty is handled by averaging over *stages* inversions with noise
      added to the input data for each inversion.  Usually the measurement
      uncertainty is estimated during data reduction and phase reconstruction,
      and Gaussian noise is added to the data. This is scaled by a factor of
      *noise* so the effects of noisier or quieter input are easy to estimate.
      If the uncertainty estimate is not available, 5% relative noise per point
      is assumed.

      If *monitor* is specified, then Poisson noise is used instead, according to
      the following::

      *noise* U[-1, 1] (poisson(*monitor* |real R|)/*monitor* - |real R|)

      That is, a value is pulled from the Poisson distribution of the expected
      counts, and the noise is the difference between this and the actual counts.
      This is further scaled by a fudge factor of *noise* and a further random
      uniform in [-1, 1].

      ====================  =======================================================
      Uncertainty controls  Description
      ====================  =======================================================
      *stages* (4)          number of inversions to average over
      *noise* (1)           noise scale factor
      *monitor* (None)      incident beam intensity (poisson noise source)
      ====================  =======================================================

    **Inversion controls:**

      ===================  ========================================================
      Inversions controls  Description
      ===================  ========================================================
      *rhopoints* (128)    number of steps in the returned profile. If this value
                           is too low, the profile will be coarse.  If it is too
                           high, the computation will take a long time. The
                           additional smoothness generated by a high value of
                           *rhopoints* is illusory --- the information content of
                           the profile is limited by the number of Q points which
                           have been measured. Set *rhopoints* to (1/*dz*) for a
                           step size near *dz* in the profile.
      *calcpoints* (4)     number of internal steps per profile step. It is used
                           internally to improve the accuracy of the calculation.
                           For larger values of *rhopoints*, smaller values of
                           *calcpoints* are feasible.
      *iters* (6)          number of iterations to use for inversion. A value of 6
                           seems to work well. You can observe this by setting
                           *showiters* to True and looking at the convergence of
                           each stage of the averaging calculation.
      *showiters* (False)  set to true to show inversion converging. Click the
                           graph to move to the next stage.
      *ctf_window* (0)     cosine transform smoothing. In practice, it is set to 0
                           for no smoothing.
      ===================  ========================================================

    **Computed profile:**
      The reflectivity computed from *z*, *rho* will not match the input data
      because the effect of the substrate has been removed in the process of
      reconstructing the phase.  Instead, you will need to compute reflectivity
      from *rho*-*substrate* on the reversed profile. This is done in
      :meth:`refl` when no surround material is selected, and can be used to show
      the difference between measured and inverted reflectivity.  You may need to
      increase *calcpoints* or modify *thickness* to get a close match.

      ======================  ===========================================================
      Computed profile        Description
      ======================  ===========================================================
      *Qinput*, *RealRinput*  input data. The input data *Qinput*, *RealRinput* need to
                              be placed on an even grid going from 0 to *Qmax* using
                              linear interpolation.  Values below *Qmin* are set to
                              zero, and the number of points between *Qmin* and *Qmax*
                              is preserved. This resampling works best when the input
                              data are equally spaced, starting at k*dQ for some k.
      *Q*, *RealR*, *dRealR*  output data. The returned *Q*, *RealR*, *dRealR* are the
                              values averaged over multiple stages with added noise.
                              The plots show this as the range of input variation used
                              in approximating the profile variation.
      *z*                     represents the depth into the profile. *z* equals
                              *thickness* at the substrate. If the thickness is correct,
                              then *z* will be zero at the top of the film, but in
                              practice the *thickness* value provided will be larger
                              than the actual film thickness, and a portion of the vacuum
                              will be included at the beginning of the profile.
      *rho*                   It is the SLD at depth *z* in units of 10^-6 inv A^2. It
                              is calculated from the average of the inverted profiles
                              from the noisy data sets, and includes the correction for
                              the substrate SLD defined by *substrate*. The inverted
                              *rho* will contain artifacts from the abrupt cutoff in the
                              signal at *Qmin* and *Qmax*.
      *drho*                  It is the uncertainty in the SLD profile at depth *z*. It
                              is calculated from the standard deviation of the inverted
                              profiles from the noisy data sets. The uncertainty *drho*
                              does not take into account the possible variation in the
                              signal above *Qmax*.
      *signals*               It is a list of the noisy (Q, RealR) input signals generated
                              by the uncertainty controls.
      *profiles*              It is a list of the corresponding (z, rho) profiles. The
                              first stage is computed without noise, so *signals[0]*
                              contains the meshed input and *profiles[0]* contains the
                              output of the inversion process without additional noise.
      ======================  ===========================================================

    **Output methods:**
      The primary output methods are

      ==============  ===========================================================
      Output methods  Description
      ==============  ===========================================================
      *save*          save the profile to a file.
      *show*          show the profile on the screen.
      *plot*          plot data and profile.
      *refl*          compute reflectivity from profile.
      *run*           run or rerun the inversion with new settings.
      ==============  ===========================================================

    **Additional methods for finer control of plots:**

      ===============  ===========================================================
      Output methods   Description
      ===============  ===========================================================
      *plot_data*      plot just the data.
      *plot_profile*   plot just the profile.
      *plot_residual*  plot data minus theory.
      ===============  ===========================================================

    """

    # Global parameters for the class and their default values
    substrate = 0
    thickness = 400
    calcpoints = 4
    rhopoints = 128
    Qmin = 0
    Qmax = None
    iters = 6
    stages = 10
    ctf_window = 0
    backrefl = True
    noise = 1
    bse = 0
    showiters = False
    monitor = None

    def __init__(self, data=None, **kw):
        # Load the data
        if isstr(data):
            self._loaddata(data)
        else: # assume it is a pair, e.g., a tuple, a list, or an Nx2 array
            self._setdata(data)

        # Run with current keywords
        self._set(**kw)


    def _loaddata(self, file):
        """
        Load data from a file of Q, real(R), dreal(R).
        """
        data = np.loadtxt(file).T
        self._setdata(data, name=file)


    def _setdata(self, data, name="data"):
        """
        Set *Qinput*, *RealRinput* from Q, real(R) vectors.
        """

        self.name = name
        if len(data) == 3:
            q, rer, drer = data
        else:
            q, rer = data
            drer = None
        # Force equal spacing by interpolation
        self.Qinput, self.RealRinput = np.asarray(q), np.asarray(rer)
        self.dRealRinput = np.asarray(drer) if drer is not None else None


    def _remesh(self):
        """
        Returns Qmeshed, RealRmeshed.

        Resamples the data on an even grid, setting values below Qmin and above
        Qmax to zero.  The number of points between Qmin and Qmax is preserved.
        This works best when data are equally spaced to begin with, starting a
        k*dQ for some k.
        """

        q, rer, drer = self.Qinput, self.RealRinput, self.dRealRinput
        if drer is None:
            drer = 0*rer

        # Trim from Qmin to Qmax
        if self.Qmin is not None:
            idx = q >= self.Qmin
            q, rer, drer = q[idx], rer[idx], drer[idx]
        if self.Qmax is not None:
            idx = q <= self.Qmax
            q, rer, drer = q[idx], rer[idx], drer[idx]

        # Resample on even spaced grid, preserving approximately the points
        # between Qmin and Qmax
        dq = (q[-1]-q[0])/(len(q) - 1)
        npts = int(q[-1]/dq + 1.5)
        q, rer = remesh([q, rer], 0, q[-1], npts, left=0, right=0)

        # Process uncertainty
        if self.dRealRinput is not None:
            q, drer = remesh([q, drer], 0, q[-1], npts, left=0, right=0)
        else:
            drer = None

        return q, rer, drer


    def run(self, **kw):
        """
        Run multiple inversions with resynthesized data for each.

        All control keywords from the constructor can be used, except
        *data* and *outfile*.
        Sets *signals* to the list of noisy (Q, RealR) signals and sets
        *profiles* to the list of generated (z, rho) profiles.
        """

        from numpy.random import uniform, poisson, normal

        self._set(**kw)
        q, rer, drer = self._remesh()
        signals = []
        profiles = []
        stages = self.stages if self.noise > 0 else 1
        for i in range(stages):
            if i == 0:
                # Use data noise for the first stage
                noisyR = rer
            elif self.monitor is not None:
                # Use incident beam as noise source
                pnoise = poisson(self.monitor*abs(rer))/self.monitor - abs(rer)
                unoise = uniform(-1, 1, rer.shape)
                noisyR = rer + self.noise*unoise*pnoise
            elif drer is not None:
                # Use gaussian uncertainty estimate as noise source
                noisyR = rer + normal(0, 1)*self.noise*drer
            else:
                # Use 5% relative amplitude as noise source
                noisyR = rer + normal(0, 1)*self.noise*0.05*abs(rer)

            ctf = self._transform(noisyR, Qmax=q[-1],
                                  bse=self.bse, porder=1)
            qp = self._invert(ctf, iters=self.iters)
            if self.showiters: # Show individual iterations
                import pylab
                pylab.cla()
                for qpi in qp:
                    pylab.plot(qpi[0], qpi[1])
                pylab.ginput(show_clicks=False)
            z, rho = remesh(qp[-1], 0, self.thickness, self.rhopoints)

            if not self.backrefl:
                z, rho = z[::-1], rho[::-1]
            signals.append((q, noisyR))
            profiles.append((z, rho))
        self.signals, self.profiles = signals, profiles


    def chisq(self):
        """
        Compute normalized sum squared difference between original real R and
        the real R for the inverted profile.
        """

        from numpy.random import normal
        idx = self.dRealR > 1e-15
        #print("min dR", min(self.dRealR[self.dRealR>1e-15]))
        q, rer, drer = self.Q[idx], self.RealR[idx], self.dRealR[idx]
        rerinv = real(self.refl(q))
        chisq = np.sum(((rer - rerinv)/drer)**2)/len(q)
        return chisq


    # Computed attributes.
    def _get_z(self):
        """Inverted SLD profile depth in Angstroms"""
        return self.profiles[0][0]

    def _get_rho(self):
        """Inverted SLD profile in 10^-6 * inv A^2 units"""
        rho = mean([p[1] for p in self.profiles], axis=0) + self.substrate
        return rho

    def _get_drho(self):
        """Inverted SLD profile uncertainty"""
        drho = std([p[1] for p in self.profiles], axis=0)
        return drho

    def _get_Q(self):
        """Inverted profile calculation points"""
        return self.signals[0][0]

    def _get_RealR(self):
        """Average inversion free film reflectivity input"""
        return mean([p[1] for p in self.signals], axis=0)

    def _get_dRealR(self):
        """Free film reflectivity input uncertainty"""
        return std([p[1] for p in self.signals], axis=0)

    z = property(_get_z)
    rho = property(_get_rho)
    drho = property(_get_drho)
    Q = property(_get_Q)
    RealR = property(_get_RealR)
    dRealR = property(_get_dRealR)


    def show(self):
        """Print z, rho, drho to the screen."""
        print("# %9s %11s %11s"%("z", "rho", "drho"))
        for point in zip(self.z, self.rho, self.drho):
            print("%11.4f %11.4f %11.4f"%point)


    def save(self, outfile=None):
        """
        Save z, rho, drho to three column text file named *outfile*.

        **Parameters:**
            *outfile:* file
                If *outfile* is not provided, the name of the input file
                will be used, but with the extension replaced by '.amp'.

        **Returns:**
            *None*
        """

        if outfile is None:
            basefile = os.path.splitext(os.path.basename(self.name))[0]
            outfile = basefile+os.extsep+"amp"
        fid = open(outfile, "w")
        fid.write("#  Z  Rho  dRho\n")
        np.savetxt(fid, np.array([self.z, self.rho, self.drho]).T)
        fid.close()


    def refl(self, Q=None, surround=None):
        """
        Return the complex reflectivity amplitude.

        **Parameters:**
            *Q:* boolean
                Use *Q* if provided, otherwise use the evenly spaced Q values
                used for the inversion.
            *surround:* boolean
                If *surround* is provided, compute the reflectivity for the free
                film in the context of the substrate and the surround, otherwise
                compute the reflectivity of the reversed free film embedded in
                the substrate to match against the reflectivity amplitude
                supplied as input.

        **Returns:**
            *None*
        """

        if Q is None:
            Q = self.Q
        if self.backrefl:
            # Back reflectivity is equivalent to -Q inputs
            Q = -Q
        if surround is None:
            # Phase reconstructed free film reflectivty is reversed,
            # and has an implicit substrate in front and behind.
            surround = self.substrate
            Q = -Q
        dz = np.hstack((0, diff(self.z), 0))
        rho = np.hstack((surround, self.rho[1:], self.substrate))
        r = refl(Q, dz, rho)
        return  r


    def plot(self, details=False, phase=None):
        """
        Plot the data and the inversion.

        **Parameters:**
            *details:* boolean
                If *details* is True, then plot the individual stages used to
                calculate the average, otherwise just plot the envelope.
            *phase:* boolean
                 If *phase* is a phase reconstruction object, plot the original
                 measurements.

        **Returns:**
            *None*
        """

        import pylab

        if phase:
            pylab.subplot(221)
            phase.plot_measurement(profile=(self.z, self.rho))
            pylab.subplot(223)
            phase.plot_imaginary()
        pylab.subplot(222 if phase else 211)
        self.plot_profile(details=details)
        pylab.subplot(224 if phase else 212)
        self.plot_input(details=details)


    def plot6(self, details=False, phase=None):
        # This is an alternate to plot6 for evaluation purposes.
        import pylab

        if phase:
            pylab.subplot(321)
            phase.plot_measurement(profile=(self.z, self.rho))
            pylab.subplot(323)
            phase.plot_imaginary()
            pylab.subplot(325)
            phase.plot_phase()
        pylab.subplot(322 if phase else 311)
        self.plot_profile(details=details)
        pylab.subplot(324 if phase else 312)
        self.plot_input(details=details)
        pylab.subplot(326 if phase else 313)
        self.plot_residual()


    def plot_input(self, details=False, lowQ_inset=0):
        """
        Plot the real R vs. the real R computed from inversion.

        **Parameters**
            *details:* boolean
                If *details* is True, then plot the individual stages used to
                calculate the average, otherwise just plot the envelope.
            *lowQ_inset:* intger
                If *lowQ_inset* > 0, then plot a graph of Q, real R values
                below lowQ_inset, without scaling by Q**2.

        **Returns:**
            *None*
        """
        from matplotlib.font_manager import FontProperties
        import pylab

        if details:
            plotamp(self.Qinput, self.RealRinput)
            for p in self.signals:
                plotamp(self.Q, p[1])
        else:
            plotamp(self.Q, self.RealR, dr=self.dRealR, label=None,
                    linestyle='', color="blue")
            plotamp(self.Qinput, self.RealRinput, label="Input",
                    color="blue")
            Rinverted = real(self.refl(self.Qinput))
            plotamp(self.Qinput, Rinverted, color=DARK_RED, label="Inverted")
            pylab.legend(prop=FontProperties(size='medium'))
            chisq = self.chisq() # Note: cache calculated profile?
            pylab.text(0.01, 0.01, "chisq=%.1f"%chisq,
                       transform=pylab.gca().transAxes,
                       ha='left', va='bottom')

            if lowQ_inset > 0:
                # Low Q inset
                orig = pylab.gca()
                box = orig.get_position()
                ax = pylab.axes([box.xmin+0.02, box.ymin+0.02,
                                 box.width/4, box.height/4],
                                axisbg=[0.95, 0.95, 0.65, 0.85])
                ax.plot(self.Qinput, self.RealRinput, color="blue")
                ax.plot(self.Qinput, Rinverted)
                ax.text(0.99, 0.01, "Q, Real R for Q<%g"%lowQ_inset,
                        transform=ax.transAxes, ha='right', va='bottom')
                qmax = lowQ_inset
                ymax = max(max(self.RealRinput[self.Qinput < qmax]),
                           max(Rinverted[self.Qinput < qmax]))
                pylab.setp(ax, xticks=[], yticks=[],
                           xlim=[0, qmax], ylim=[-1, 1.1*(ymax+1)-1])
                pylab.axes(orig)

        plottitle('Reconstructed Phase')


    def plot_profile(self, details=False, **kw):
        """
        Plot the computed profiles.

        **Parameters:**
            *details:* boolean
                If *details* is True, then plot the individual stages used to
                calculate the average, otherwise just plot the envelope.

        **Returns:**
            *None*
        """

        import pylab

        pylab.grid(True)
        if details:
            for p in self.profiles:
                pylab.plot(p[0], p[1]+self.substrate)
        else:
            z, rho, drho = self.z, self.rho, self.drho
            [h] = pylab.plot(z, rho, color=DARK_RED, **kw)
            pylab.fill_between(z, rho-drho, rho+drho,
                               color=h.get_color(), alpha=0.2)
            #pylab.plot(z, rho+drho, '--', color=h.get_color())
            #pylab.plot(z, rho-drho, '--', color=h.get_color())
        pylab.text(0.01, 0.01, 'surface',
                   transform=pylab.gca().transAxes,
                   ha='left', va='bottom')
        pylab.text(0.99, 0.01, 'substrate',
                   transform=pylab.gca().transAxes,
                   ha='right', va='bottom')
        pylab.ylabel('SLD (inv A^2)')
        pylab.xlabel('Depth (A)')
        plottitle('Depth Profile')


    def plot_residual(self, details=False):
        """
        Plot the residuals (inversion minus input).

        **Parameters:**
            *details:* boolean
                If *details* is True, then plot the individual stages used to
                calculate the average, otherwise just plot the envelope.

        **Returns:**
            *None*
        """

        import pylab

        Q, RealR = self.Qinput, self.RealRinput
        r = self.refl(Q)
        pylab.plot(Q, Q**2*(real(r)-RealR))
        pylab.ylabel('Residuals [Q^2 * (Real R - input)]')
        pylab.xlabel("Q (inv A)")
        plottitle('Phase Residuals')


    def _set(self, **kw):
        """
        Set a group of attributes.
        """

        for k, v in kw.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise ValueError("Invalid keyword argument for Inversion class")
        self.rhoscale = 1e6 / (4 * pi * self.thickness**2)


    def _transform(self, RealR, Qmax=None, bse=0, porder=1):
        """
        Returns the cosine transform function used by inversion.

        *bse* is bound-state energy, with units of 10^-6 inv A^2.  It was used
        in the past to handle profiles with negative SLD at the beginning, but
        the the plain correction of bse=0 has since been found to be good
        enough for the profiles we are looking at. *porder* is the order of the
        interpolating polynomial, which must be 1 for the current interpolation
        class.
        """

        if not 0 <= porder <= 6:
            raise ValueError("Polynomial order must be between 0 and 6")
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
        x = arange(0, ceil(2/dz))*dz
        maxm = len(x)
        if maxm%2 == 0:
            maxm += 1
        mx = int(maxm/2+0.5)
        h = 2/(2*mx-3)
        g = np.hstack((ctf(x[:-1]*self.thickness), 0, 0, 0))
        q = 2 * diff(g[:-2])/h
        q[-1] = 0
        ut = arange(2*mx-2)*h*self.thickness/2
        if self.ctf_window > 0:
            # Smooth ctf with 3-sample approximation
            du = self.ctf_window*h*self.thickness/2
            qinter = Interpolator(ut, q, porder=1)
            q = (qinter(ut - du) + qinter(ut) + qinter(ut + du))/3
        q = np.hstack((q, 0))
        qp = [(ut, -2*q*self.rhoscale)]

        Delta = np.zeros((mx, 2*mx), 'd')
        for iter in range(iters):
            for m in range(2, mx):
                n = np.array(range(m, 2*mx-(m+1)))
                Delta[m, n] = (
                    h**2 * q[m-1] * (g[m+n] + Delta[m-1, n])
                    + Delta[m-1, n+1] + Delta[m-1, n-1] - Delta[m-2, n])
            udiag = -g[:2*mx-2:2] - diag(Delta)[:mx-1]
            mup = len(udiag) - 2
            h = 1/mup
            ut = arange(mup)*h*self.thickness
            q = 2 * diff(udiag[:-1])/h
            qp.append((ut, self.rhoscale*q))
            q = np.hstack((q, 0, 0))
        return qp


def plottitle(title):
    import pylab

    # Place title above the plot so that it is not overlapped by the legend.
    # Note that the title is drawn as text rather than as a title object so
    # that it will be kept as close as possible to the plot when the window is
    # resized to a smaller size.
    pylab.text(0.5, 1.07, title, fontsize='medium',
               transform=pylab.gca().transAxes,
               ha='center', va='top', backgroundcolor=(0.9, 0.9, 0.6))


def plotamp(Q, r, dr=None, scaled=True, ylabel="Real R", **kw):
    """
    Plot Q, realR data.
    """

    import pylab

    scale = 1e4*Q**2 if scaled else 1
    if scaled:
        ylabel = "(100 Q)^2 "+ylabel
    [h] = pylab.plot(Q, scale*r, **kw)
    if dr is not None:
        pylab.fill_between(Q, scale*(r-dr), scale*(r+dr),
                           color=h.get_color(), alpha=0.2)
    pylab.ylabel(ylabel)
    pylab.xlabel("Q (inv A)")


class Interpolator():
    """
    Construct an interpolation function from pairs (xi, yi).
    """

    def __init__(self, xi, yi, porder=1):
        if len(xi) != len(yi):
            raise ValueError("xi:%d and yi:%d must have the same length"
                             %(len(xi), len(yi)))
        self.xi, self.yi = xi, yi
        self.porder = porder
        if porder != 1:
            raise NotImplementedError(
                "Interpolator only supports polynomial order of 1")
    def __call__(self, x):
        return np.interp(x, self.xi, self.yi)


def phase_shift(q, r, shift=0):
    return r*exp(1j*shift*q)


def remesh(data, xmin, xmax, npts, left=None, right=None):
    """
    Resample the data on a fixed grid.
    """

    x, y = data
    x, y = x[isfinite(x)], y[isfinite(y)]
    if npts > len(x):
        npts = len(x)
    newx = np.linspace(xmin, xmax, npts)
    newy = np.interp(newx, x, y, left=left, right=right)
    return np.array((newx, newy))


# This program is public domain.
# Author: Paul Kienzle
"""
Optical matrix form of the reflectivity calculation.

O.S. Heavens, Optical Properties of Thin Solid Films
"""

def refl(Qz, depth, rho, mu=0, wavelength=1, sigma=0):
    """
    Reflectometry as a function of Qz and wavelength.

    **Parameters:**
        *Qz:* float|A
            Scattering vector 4*pi*sin(theta)/wavelength. This is an array.
        *depth:* float|A
            Thickness of each layer.  The thickness of the incident medium
            and substrate are ignored.
        *rho, mu (uNb):* (float, float)|
            Scattering length density and absorption of each layer.
        *wavelength:* float|A
            Incident wavelength (angstrom).
        *sigma:* float|A
            Interfacial roughness. This is the roughness between a layer
            and the subsequent layer. There is no interface associated
            with the substrate. The sigma array should have at least n-1
            entries, though it may have n with the last entry ignored.

    :Returns:
        *r* array of float
    """

    if isscalar(Qz):
        Qz = np.array([Qz], 'd')
    n = len(rho)
    nQ = len(Qz)

    # Make everything into arrays
    kz = np.asarray(Qz, 'd')/2
    depth = np.asarray(depth, 'd')
    rho = np.asarray(rho, 'd')
    mu = mu*np.ones(n, 'd') if isscalar(mu) else np.asarray(mu, 'd')
    wavelength = wavelength*np.ones(nQ, 'd') \
        if isscalar(wavelength) else np.asarray(wavelength, 'd')
    sigma = sigma*np.ones(n-1, 'd') if isscalar(sigma) else np.asarray(sigma, 'd')

    # Scale units
    rho = rho*1e-6
    mu = mu*1e-6

    ## For kz < 0 we need to reverse the order of the layers
    ## Note that the interface array sigma is conceptually one
    ## shorter than rho, mu so when reversing it, start at n-1.
    ## This allows the caller to provide an array of length n
    ## corresponding to rho, mu or of length n-1.
    idx = (kz >= 0)
    r = np.empty(len(kz), 'D')
    r[idx] = _refl_calc(kz[idx], wavelength[idx], depth, rho, mu, sigma)
    r[~idx] = _refl_calc(
        abs(kz[~idx]), wavelength[~idx],
        depth[-1::-1], rho[-1::-1], mu[-1::-1],
        sigma[n-2::-1])
    r[abs(kz) < 1.e-6] = -1  # reflectivity at kz=0 is -1
    return r


def _refl_calc(kz, wavelength, depth, rho, mu, sigma):
    """Abeles matrix calculation."""
    if len(kz) == 0:
        return kz

    ## Complex index of refraction is relative to the incident medium.
    ## We can get the same effect using kz_rel^2 = kz^2 + 4*pi*rho_o
    ## in place of kz^2, and ignoring rho_o.
    kz_sq = kz**2 + 4*pi*rho[0]
    k = kz

    # According to Heavens, the initial matrix should be [ 1 F; F 1],
    # which we do by setting B=I and M0 to [1 F; F 1].  An extra matrix
    # multiply versus some coding convenience.
    B11 = 1
    B22 = 1
    B21 = 0
    B12 = 0
    for i in range(0, len(rho)-1):
        k_next = sqrt(kz_sq - (4*pi*rho[i+1] + 2j*pi*mu[i+1]/wavelength))
        F = (k - k_next) / (k + k_next)
        F *= exp(-2*k*k_next*sigma[i]**2)
        M11 = exp(1j*k*depth[i]) if i > 0 else 1
        M22 = exp(-1j*k*depth[i]) if i > 0 else 1
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


def reconstruct(file1, file2, u, v1, v2, stages=100):
    r"""
    Two reflectivity measurements of a film with different surrounding media
    :math:`|r_1|^2` and :math:`|r_2|^2` can be combined to compute the expected
    complex reflection amplitude r_reversed of the free standing film measured
    from the opposite side. The calculation can be done by varying the fronting
    media or by varying the backing media. For this code we only support
    measurements through a uniform substrate *u*, on two varying surrounding
    materials *v1*, *v2*.

    We have to be careful about terminology. We will use the term substrate to
    mean the base on which we deposit our film of interest, and surface to be
    the material we put on the other side. The fronting or incident medium is
    the material through which the beam enters the sample. The backing
    material is the material on the other side. In back reflectivity, the
    fronting material is the substrate and the backing material is the surface.
    We are using u for the uniform substrate and v for the varying surface
    material.

    In the experimental setup at the NCNR, we have a liquid resevoir which we
    can place above the film.  We measure first with one liquid in the resevoir
    such as heavy water (D2O) and again with air or a contrasting liquid such
    as water (H2O).  At approximately 100 um, the resevoir depth is much
    thicker than the effective coherence length of the neutron in the z
    direction, and so can be treated as a semi-infinite substrate, even when it
    is empty.

    .. Note:: You cannot simulate a semi-infinite substrate using a large but
       finitely thick material using the reflectometry calculation; at
       best the resulting reflection will be a high frequency signal which
       smooths after applying the resolution correction to a magnitude
       that is twice the reflection from a semi-infinite substrate.

       The incident beam is measured through the substrate, and thus subject to
       the same absorption as the reflected beam. Refraction on entering and
       leaving the substrated is accounted for by a small adjustment to Q
       inside the reflectivity calculation.


    When measuring reflectivity through the substrate, the beam enters the
    substrate from the side, refracts a little because of the steep angle of
    entry, reflects off the sample, and leaves through the other side of the
    substrate with an equal but opposite refraction.  The reflectivity
    calculation takes this into account.  Traveling through several centimeters
    of substrate, some of the beam will get absorbed.  We account for this
    either by entering an incident medium transmission coefficient in the
    reduction process, or by measuring the incident beam through the substrate
    so that it is subject to approximately the same absorption.

    The phase cannot be properly computed for Q values which are below the
    critical edge Qc^2 for both surround variations.  This problem can be
    avoided by choosing a substrate which is smaller than the surround on at
    least one of the measurements.  This measurement will not have a critical
    edge at positive Q.  In order to do a correct footprint correction the
    other measurement should use a substrate SLD greater than the surround SLD.

    If the input file records uncertainty in the measurement, we perform a
    Monte Carlo uncertainty estimate of the reconstructed complex amplitude.

    **Inputs:**

    ================  =============================================================
    Input parameters  Description
    ================  =============================================================
    *file1*, *file2*  reflectivity measurements at identical Q values. *file1*
                      and *file2* can be pairs of vectors (q1, r1), (q2, r2) or files
                      containing at least two columns (q, r), with the remaining
                      columns such as dr, dq, and lambda ignored. If a third
                      vector, dr, is present in both datasets, then an uncertainty
                      estimate will be calculated for the reconstructed phase.
    *v1*, *v2*        SLD of varying surrounds in *file1* and *file2*
    *u*               SLD of the uniform substrate
    *stages*          number of trials in Monte Carlo uncertainty estimate
    ================  =============================================================

    Returns a :class:`SurroundVariation` object with the following attributes:

    ==================  =========================================
    Attributes          Description
    ==================  =========================================
    *RealR*, *ImagR*    real and imaginary reflectivity
    *dRealR*, *dImagR*  Monte Carlo uncertainty estimate
    *name1*, *name2*    names of the input files
    *save(file)*        save Q, RealR, ImagR to a file
    *show()*, *plot()*  display the results
    ==================  =========================================

    **Notes:**

    There is a question of how beam effects (scale, background, resolution)
    will show up in the phase reconstruction. To understand this we can play
    with the reverse problem applying beam effects (intensity=A, background=B,
    resolution=G) to the reflectivity amplitude $r$ such that the computed
    $|r|^2$ matches the measured $R = A G*|r|^2 + B$, where $*$ is the
    convolution operator.

    There is a reasonably pretty solution for intensity and background: set
    $s =  r \surd A + i r \surd B / |r|$ so that
    $|s|^2 = A |r|^2 + |r|^2 B/|r|^2 = A |r|^2 + B$. Since $r$ is complex,
    the intensity and background will show up in both real and imaginary
    channels of the phase reconstruction.

    It is not so pretty for resolution since the sum of the squares does not
    match the square of the sum:

    .. math::

        G * |r|^2 = \int G(q'-q)|r(q)|^2 dq \ne |\int G(q'-q)r(q)dq|^2 = |G*r|^2

    This is an area may have been investigated in the 90's when the theory of
    neutron phase reconstruction and inversion was developing, but this
    reconstruction code does not do anything to take resolution into account.
    Given that we known $\Delta q$ for each measured $R$ we should be able to
    deconvolute using a matrix approximation to the integral:

    .. math::

        R = G R' \Rightarrow R' = G^{-1} R

    where each row of $G$ is the gaussian weights $G(q_k - q)$ with width
    $\Delta q_k$ evaluated at all measured points $q$. Trying this didn't
    produce a useful (or believable) result. Maybe it was a problem with the
    test code, or maybe it is an effect of applying an ill-conditioned
    linear operator over data that varies by orders of magnitude.

    So question: are there techniques for deconvoluting reflectivity curves?

    Going the other direction, we can apply a resolution function to $Re(r)$
    and $Im(r)$ to see how well they reproduce the resolution applied to
    $|r|^2$. The answer is that it does a pretty good job, but the overall
    smoothing is somewhat less than expected.

    .. figure:: ../images/resolution.png
        :alt: Reflectivity after applying resolution to amplitude.

        Amplitude effects of applying a 2% $\Delta Q/Q$ resolution to the
        complex amplitude prior to squaring.

    I'm guessing that our reconstructed amplitude is going to show a similar
    decay due to resolution. This ought to show up as a rounding off of edges
    in the inverted profile (guessing again from the effects of applying
    windowing functions to reduce ringing in the Fourier transform). This is
    intuitive: poor resolution should show less detail in the profile.
    """

    return SurroundVariation(file1, file2, u, v1, v2, stages=stages)


class SurroundVariation():
    """
    See :func:`reconstruct` for details.

    **Attributes:**

    =====================  ========================================
    Attributes             Description
    =====================  ========================================
    *Q*, *RealR*, *ImagR*  real and imaginary reflectivity
    *dRealR*, *dImagR*     Monte Carlo uncertainty estimate or None
    *Qin*, *R1*, *R2*      input data
    *dR1*, *dR2*           input uncertainty or None
    *name1*, *name2*       input file names
    *save(file)*           save output
    *show()*, *plot()*     show Q, RealR, ImagR
    =====================  ========================================
    """

    backrefl = True

    def __init__(self, file1, file2, u, v1, v2, stages=100):
        self.u = u
        self.v1, self.v2 = v1, v2
        self._load(file1, file2)
        self._calc()
        self._calc_err(stages=stages)
        self.clean()


    def optimize(self, z, rho_initial):
        """
        Run a quasi-Newton optimizer on a discretized profile.

        **Parameters:**
            *z:* boolean
                Represents the depth into the profile. z equals thickness at
                the substrate.

            *rho_initial:* boolean
                The initial profile *rho_initial* should come from direct
                inversion.
        **Returns:**
            *rho:* (boolean, boolean)|
                Returns the final profile rho which minimizes chisq.
        """

        from scipy.optimize import fmin_l_bfgs_b as fmin

        def cost(rho):
            R1, R2 = self.refl(z, rho, resid=True)
            return np.sum(R1**2) + np.sum(R2**2)

        rho_final = rho_initial
        rho_final, f, d = fmin(cost, rho_initial, approx_grad=True, maxfun=20)
        return z, rho_final


    def refl(self, z, rho, resid=False):
        """
        Return the reflectivities R1 and R2 for the film *z*, *rho* in the
        context of the substrate and surround variation.

        **Parameters:**
            *z:* boolean
                Represents the depth into the profile. z equals thickness at
                the substrate.

            *rho:* boolean
                If the resolution is known, then return the convolved theory
                function.
            *resid:* boolean
                If *resid* is True, then return the weighted residuals vector.

        **Returns:**
            *R1, R2:* (boolean, boolean)|
                Return the reflectivities R1 and R2 for the film *z*, *rho*.
        """

        w = np.hstack((0, np.diff(z), 0))
        rho = np.hstack((0, rho[1:], self.u))
        rho[0] = self.v1
        R1 = self._calc_refl(w, rho)
        rho[0] = self.v2
        R2 = self._calc_refl(w, rho)
        if resid:
            R1 = (self.R1in-R1)/self.dR1in
            R2 = (self.R2in-R2)/self.dR2in
        return R1, R2


    def _calc_free(self, z, rho):
        # This is more or less cloned code that should be written just once.
        w = np.hstack((0, np.diff(z), 0))
        rho = np.hstack((self.u, rho[1:], self.u))
        rho[0] = self.u
        Q = -self.Qin
        if self.backrefl:
            Q = -Q
        r = refl(Q, w, rho)
        return r.real, r.imag


    def _calc_refl(self, w, rho):
        Q, dQ = self.Qin, self.dQin
        # Back reflectivity is equivalent to -Q inputs
        if self.backrefl:
            Q = -Q
        r = refl(Q, w, rho)
        if dQ is not None:
            R = convolve(Q, abs(r)**2, Q, dQ)
        else:
            R = abs(r)**2
        return R


    def clean(self):
        """
        Remove points which are NaN or Inf from the computed phase.
        """

        # Toss invalid values
        Q, re, im = self.Qin, self.RealR, self.ImagR
        if self.dRealR is not None:
            dre, dim = self.dRealR, self.dImagR
            keep = reduce(lambda y, x: isfinite(x)&y, [re, im], True)
            self.Q, self.RealR, self.dRealR, self.ImagR, self.dImagR \
                = [v[keep] for v in (Q, re, dre, im, dim)]
        else:
            keep = reduce(lambda y, x: isfinite(x)&y, [re, im], True)
            self.Q, self.RealR, self.ImagR = [v[keep] for v in (Q, re, im)]


    def save(self, outfile=None, uncertainty=True):
        """
        Save Q, RealR, ImagR to a three column text file named *outfile*, or
        save Q, RealR, ImagR, dRealR, dImagR to a five column text file.

        **Parameters:**
            *outfile:* file
                Include dRealR, dImagR if they exist and if *uncertainty*
                is True, making a five column file.
            *uncertainity:* boolean
                Include dRealR and dImagR if True.

        **Returns:**
            *None*
        """

        if outfile is None:
            basefile = os.path.splitext(os.path.basename(self.name1))[0]
            outfile = basefile+os.extsep+"amp"

        header = "#  Q  RealR  ImagR"
        v = [self.Q, self.RealR, self.ImagR]
        if self.dRealR is not None and uncertainty:
            header += "  dRealR  dImagR"
            v += [self.dRealR, self.dImagR]

        fid = open(outfile, "w")
        fid.write(header+"\n")
        np.savetxt(fid, np.array(v).T)
        fid.close()


    def save_inverted(self, outfile=None, profile=None):
        """
        Save Q, R1, R2, RealR of the inverted profile.
        """

        R1, R2 = self.refl(*profile)
        rer, imr = self._calc_free(*profile)
        data = np.vstack((self.Qin, R1, R2, rer, imr))
        fid = open(outfile, "w")
        fid.write("#  Q  R1  R2  RealR  ImagR\n")
        np.savetxt(fid, np.array(data).T)
        fid.close()


    def show(self):
        """Print Q, RealR, ImagR to the screen."""
        print("# %9s %11s %11s"%("Q", "RealR", "ImagR"))
        for point in zip(self.Q, self.RealR, self.ImagR):
            print("%11.4g %11.4g %11.4g"%point)


    def plot_measurement(self, profile=None):
        """Plot the data, and if available, the inverted theory."""
        from matplotlib.font_manager import FontProperties
        import pylab

        def plot1(Q, R, dR, Rth, surround, label, color):
            # Fresnel reflectivity
            if self.backrefl:
                F = abs(refl(Q, [0, 0], [self.u, surround]))**2
            else:
                F = abs(refl(Q, [0, 0], [surround, self.u]))**2
            pylab.plot(Q, R/F, '.', label=label, color=color)
            if Rth is not None:
                pylab.plot(Q, Rth/F, '-', label=None, color=color)
            if dR is not None:
                pylab.fill_between(Q, (R-dR)/F, (R+dR)/F,
                                   color=color, alpha=0.2)
                if Rth is not None:
                    chisq = np.sum(((R-Rth)/dR)**2)
                else:
                    chisq = 0
                return chisq, len(Q)
            else:
                # Doesn't make sense to compute chisq for unweighted
                # reflectivity since there are several orders of magnitude
                # differences between the data points.
                return 0, 1

        if profile is not None:
            R1, R2 = self.refl(*profile)
        else:
            R1, R2 = None, None

        # Only show file.ext portion of the file specification
        name1 = os.path.basename(self.name1)
        name2 = os.path.basename(self.name2)
        pylab.cla()
        chisq1, n1 = plot1(self.Qin, self.R1in, self.dR1in, R1,
                           self.v1, name1, 'blue')
        chisq2, n2 = plot1(self.Qin, self.R2in, self.dR2in, R2,
                           self.v2, name2, 'green')
        pylab.legend(prop=FontProperties(size='medium'))
        chisq = (chisq1+chisq2)/(n1+n2)
        if chisq != 0:
            pylab.text(0.01, 0.01, "chisq=%.1f"%chisq,
                       transform=pylab.gca().transAxes,
                       ha='left', va='bottom')

        pylab.ylabel('R / Fresnel_R')
        pylab.xlabel('Q (inv A)')
        plottitle('Reflectivity Measurements')


    def plot_phase(self):
        from matplotlib.font_manager import FontProperties
        import pylab
        plotamp(self.Q, self.ImagR, dr=self.dImagR,
                color='blue', label='Imag R')
        plotamp(self.Q, self.RealR, dr=self.dRealR,
                color=DARK_RED, label='Real R')
        pylab.legend(prop=FontProperties(size='medium'))
        plottitle('Reconstructed Phase')


    def plot_imaginary(self):
        from matplotlib.font_manager import FontProperties
        import pylab
        plotamp(self.Q, -self.ImagR, dr=self.dImagR,
                color='blue', label='Imag R+')
        plotamp(self.Q, self.ImagR, dr=self.dImagR,
                color='green', label='Imag R-')
        pylab.legend(prop=FontProperties(size='medium'))
        pylab.ylabel("(100 Q)^2 Imag R")
        pylab.xlabel("Q (inv A)")
        plottitle('Reconstructed Phase')


    def _load(self, file1, file2):
        """
        Load the data from files or from tuples of (Q, R) or (Q, R, dR),
        (Q, dQ, R, dR) or (Q, dQ, R, dR, L).
        """

        # This code assumes the following data file formats:
        # 2-column data: Q, R
        # 3-column data: Q, R, dR
        # 4-column data: Q, dQ, R, dR
        # 5-column data: Q, dQ, R, dR, Lambda
        if isstr(file1):
            d1 = np.loadtxt(file1).T
            name1 = file1
        else:
            d1 = file1
            name1 = "SimData1"

        if isstr(file2):
            d2 = np.loadtxt(file2).T
            name2 = file2
        else:
            d2 = file2
            name2 = "SimData2"

        ncols = len(d1)
        if ncols <= 1:
            raise ValueError("Data file has less than two columns")
        elif ncols == 2:
            q1, r1 = d1[0:2]
            q2, r2 = d2[0:2]
            dr1 = dr2 = None
            dq1 = dq2 = None
        elif ncols == 3:
            q1, r1, dr1 = d1[0:3]
            q2, r2, dr2 = d2[0:3]
            dq1 = dq2 = None
        elif ncols == 4:
            q1, dq1, r1, dr1 = d1[0:4]
            q2, dq2, r2, dr2 = d2[0:4]
        elif ncols >= 5:
            q1, dq1, r1, dr1, lambda1 = d1[0:5]
            q2, dq2, r2, dr2, lanbda2 = d2[0:5]

        if not q1.shape == q2.shape or not (q1 == q2).all():
            raise ValueError("Q points do not match in data files")

        # Note that q2, dq2, lambda1, and lambda2 are currently discarded.
        self.name1, self.name2 = name1, name2
        self.Qin, self.dQin = q1, dq1
        self.R1in, self.R2in = r1, r2
        self.dR1in, self.dR2in = dr1, dr2


    def _calc(self):
        """
        Call the phase reconstruction calculator.
        """

        re, im = _phase_reconstruction(self.Qin, self.R1in, self.R2in,
                                       self.u, self.v1, self.v2)
        self.RealR, self.ImagR = re, im
        self.Q = self.Qin


    def _calc_err(self, stages):
        if self.dR1in is None:
            return

        from numpy.random import normal
        runs = []
        for i in range(stages):
            R1 = normal(self.R1in, self.dR1in)
            R2 = normal(self.R2in, self.dR2in)
            rer, imr = _phase_reconstruction(self.Qin, R1, R2,
                                             self.u, self.v1, self.v2)
            runs.append((rer, imr))
        rers, rims = zip(*runs)
        self.RealR = valid_f(mean, rers)
        self.ImagR = valid_f(mean, rims)
        self.dRealR = valid_f(std, rers)
        self.dImagR = valid_f(std, rims)


def valid_f(f, A, axis=0):
    """
    Calculate vector function f using only the finite elements of the array *A*.
    *axis* is the axis over which the calculation should be performed, or None
    if the calculation should summarize the entire array.
    """

    A = np.asarray(A)
    A = np.ma.masked_array(A, mask=~isfinite(A))
    return np.asarray(f(A, axis=axis))


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
    usq, v1sq, v2sq = [(1-16*pi*rho*1e-6/Qsq) for rho in (rho_u, rho_v1, rho_v2)]

    with np.errstate(invalid='ignore'):
        sigma1 = 2 * sqrt(v1sq*usq) * (1+R1sq) / (1-R1sq)
        sigma2 = 2 * sqrt(v2sq*usq) * (1+R2sq) / (1-R2sq)

        alpha = usq * (sigma1-sigma2) / (v1sq-v2sq)
        beta = (v2sq*sigma1-v1sq*sigma2) / (v2sq-v1sq)
        gamma = sqrt(alpha*beta - usq**2)
        Rre = (alpha-beta) / (2*usq+alpha+beta)
        Rim = -2*gamma / (2*usq+alpha+beta)

    return Rre, Rim


def main():
    """
    Drive phase reconstruction and direct inversion from the command line.
    """

    import sys
    import os
    from optparse import OptionParser, OptionGroup

    description = """\
Compute the scattering length density profile from the real portion of the
phase reconstructed reflectivity.  Call with a phase reconstructed reflectivity
dataset AMP, or with a pair of reduced reflectivity datasets RF1 and RF2 for
complete phase inversion.   Phase inversion requires two surrounding materials
and one substrate material to be specified. The measurement is assumed to come
through the substrate."""

    parser = OptionParser(usage="%prog [options] AMP or RF1 RF2",
                          description=description,
                          version="%prog 1.0")
    inversion_keys = [] # Collect the keywords we are using

    group = OptionGroup(parser, "Sample description", description=None)
    group.add_option("-t", "--thickness", dest="thickness",
                     default=Inversion.thickness, type="float",
                     help="sample thickness (A)")
    group.add_option("-u", "--substrate", dest="substrate",
                     default=Inversion.substrate, type="float",
                     help="sample substrate material (10^6 * SLD)")
    group.add_option("-v", "--surround", dest="surround",
                     type="float", nargs=2,
                     help="varying materials v1 v2 (10^6 * SLD) [for phase]")
    # fronting is not an inversion key
    inversion_keys += ['thickness', 'substrate']
    parser.add_option_group(group)

    group = OptionGroup(parser, "Data description", description=None)
    group.add_option("--Qmin", dest="Qmin",
                     default=Inversion.Qmin, type="float",
                     help="minimum Q value to use from the data")
    group.add_option("--Qmax", dest="Qmax",
                     default=Inversion.Qmax, type="float",
                     help="maximum Q value to use from the data")
    group.add_option("-n", "--noise", dest="noise",
                     default=Inversion.noise, type="float",
                     help="noise scaling")
    group.add_option("-M", "--monitor", dest="monitor",
                     default=Inversion.monitor, type="int",
                     help="monitor counts used for measurement")
    inversion_keys += ['Qmin', 'Qmax', 'noise', 'monitor']
    parser.add_option_group(group)

    group = OptionGroup(parser, "Outputs", description=None)
    group.add_option("-o", "--outfile", dest="outfile", default=None,
                     help="profile file (infile.prf), use '-' for console")
    group.add_option("--ampfile", dest="ampfile", default=None,
                     help="amplitude file (infile.amp)")
    group.add_option("-p", "--plot", dest="doplot",
                     action="store_true",
                     help="show plot of result")
    group.add_option("-q", "--quiet", dest="doplot",
                     action="store_false", default=True,
                     help="don't show output plot")
    # doplot is a post inversion options
    parser.add_option_group(group)

    group = OptionGroup(parser, "Calculation controls", description=None)
    group.add_option("--rhopoints", dest="rhopoints",
                     default=Inversion.rhopoints, type="int",
                     help="number of profile steps [dz=thickness/rhopoints]")
    group.add_option("-z", "--dz", dest="dz",
                     default=None, type="float",
                     help="max profile step size (A) [rhopoints=thickness/dz]")
    group.add_option("--calcpoints", dest="calcpoints",
                     default=Inversion.calcpoints, type="int",
                     help="number of calculation points per profile step")
    group.add_option("--stages", dest="stages",
                     default=Inversion.stages, type="int",
                     help="number of inversions to average over")
    group.add_option("-a", dest="amp_only", default=False,
                     action="store_true",
                     help="calculate amplitude and stop")
    inversion_keys += ['rhopoints', 'calcpoints', 'stages']
    parser.add_option_group(group)

    (options, args) = parser.parse_args()
    if len(args) < 1 or len(args) > 2:
         parser.error("Need real R data file or pair of reflectivities")

    basefile = os.path.splitext(os.path.basename(args[0]))[0]
    if len(args) == 1:
        phase = None
        data = args[0]
    elif len(args) == 2:
        if not options.surround or not options.substrate:
            parser.error("Need fronting and backing for phase inversion")
        v1, v2 = options.surround
        u = options.substrate
        phase = SurroundVariation(args[0], args[1], u=u, v1=v1, v2=v2)
        data = phase.Q, phase.RealR, phase.dRealR
        if options.ampfile:
            phase.save(options.ampfile)
        if options.amp_only and options.doplot:
            import pylab
            phase.plot()
            pylab.show()

    if options.amp_only:
        return

    if options.dz:
        options.rhopoints = ceil(1/options.dz)
    # Rather than trying to remember which control parameters I
    # have options for, I update the list of parameters that I
    # allow for each group of parameters, and pull the returned
    # values out below.
    res = Inversion(data=data, **dict((key, getattr(options, key))
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
        res.plot(phase=phase)
        pylab.show()


if __name__ == "__main__":
    main()
