# This program is in the public domain
# Author: Paul Kienzle
"""
Reflectometry resolution calculator.

Given Q = 4 pi sin(theta)/lambda, the resolution in Q is determined by
the dispersion angle theta and wavelength lambda.  For monochromatic
sources, the wavelength resolution is fixed and the angular resolution
varies.  For polychromatic sources, the wavelength resolution varies and
the angular resolution is fixed.

The angular resolution is determined by the geometry (slit positions and
openings and sample profile) with perhaps an additional contribution
from sample warp.  For monochromatic instruments, measurements are taken
with fixed slits at low angles until the beam falls completely onto the
sample.  Then as the angle increases, slits are opened to preserve full
illumination.  At some point the slit openings exceed the beam width,
and thus they are left fixed for all angles above this threshold.

When the sample is tiny, stray neutrons miss the sample and are not
reflected onto the detector.  This results in a resolution that is
tighter than expected given the slit openings.  If the sample width
is available, we can use that to determine how much of the beam is
intercepted by the sample, which we then use as an alternative second
slit.  This simple calculation isn't quite correct for very low Q, but
in that case both reflected and transmitted neutrons will arrive at the
detector, so the computed resolution of dQ=0 at Q=0 is good enough.

When the sample is warped, it may act to either focus or spread the
incident beam.  Some samples are diffuse scatters, which also acts
to spread the beam.  The degree of spread can be estimated from the
full-width at half max (FWHM) of a rocking curve at known slit settings.
The expected FWHM will be (s1+s2) / (2*(d_s1-d_s2)).  The difference
between this and the measured FWHM is the sample_broadening value.
A second order effect is that at low angles the warping will cast
shadows, changing the resolution and intensity in very complex ways.

For polychromatic time of flight instruments, the wavelength dispersion
is determined by the reduction process, which bins different time
channels between fastest and slowest, usually in a way that sets a
fixed relative resolution dL/L for each bin.

Usage
=====

:module:`resolution` (this module) defines two instrument types:
:class:`Monochromatic` and :class:`Polychromatic`.  These represent
generic scanning and time of flight instruments, respectively.  In
addition, instruments at SNS and NCNR have many of their parameters
predefined in :module:`snsdata` and :module:`ncnrdata`.

To perform a simulation or load a data set, an actual instrument must
be created.  For example::

    >>> from resolution import Monochromatic
    >>> instrument = Monochromatic(
            # instrument parameters
            instrument = "AND/R",
            radiation = "neutron",
            wavelength = 5.0042,
            dLoL=0.009,
            d_s1 = 230.0 + 1856.0,
            d_s2 = 230.0,
            # measurement parameters
            Tlo=0.5, slits_at_Tlo=0.2, slits_below=0.1,
            )

An instrument such as this can be used to compute a resolution function
for arbitrary Q values, following the slit opening pattern defined by
the instrument.  Using them, the example above becomes::

    >>> import numpy, pylab
    >>> from ncnrdata import ANDR
    >>> instrument = ANDR(Tlo=0.5, slits_at_Tlo=0.2, slits_below=0.1)
    >>> resolution = instrument.resolution(Q=numpy.linspace(0,0.5,100))
    >>> pylab.plot(resolution.T, resolution.dT)
    >>> pylab.ylabel('angular divergence (degrees FWHM)')
    >>> pylab.xlabel('angle (degrees)')
    >>> pylab.show()

The resolution object *resolution* is of :class:`Resolution`.  Using it
you can compute the resolution *dQ* for a given *Q* based on *T*, *dT*,
*L*, and *dL*.  Furthermore, it can easily be turned into a reflectometry
probe for use in modeling::

    >>> resolution.probe()

Since creating the reflectometry probe is the usual case, a couple of
driver functions are provided.  For example, the following complete
example loads and plots two data files::

    >>> import pylab
    >>> from ncnrdata import ANDR
    >>> instrument = ANDR(Tlo=0.5, slits_at_Tlo=0.2, slits_below=0.1)
    >>> probe1 = instrument.load('blg117.refl')
    >>> probe2 = instrument.load('blg126.refl')
    >>> probe1.plot()
    >>> pylab.hold(True)
    >>> probe2.plot()
    >>> pylab.show()

Generating a simulation probe is similarly convenient::

    >>> from ncnrdata import ANDR
    >>> instrument = ANDR(Tlo=0.5, slits_at_Tlo=0.2, slits_below=0.1)
    >>> probe = instrument.simulate(T=numpy.arange(0,5,100))

When loading or simulating a data set, any of the instrument parameters
and measurement geometry information can be specified, replacing the
defaults within the instrument.  For example, to include sample broadening
effects in the resolution::

    >>> from ncnrdata import ANDR
    >>> instrument = ANDR(Tlo=0.5, slits_at_Tlo=0.2, slits_below=0.1)
    >>> probe1 = instrument.load('blg117.refl', sample_broadening=0.1)

Properties of the instrument can be displayed::

    >>> print ANDR.defaults()
    >>> print instrument.defaults()

Details
=======

Polychromatic measurements have the following attributes::

    *instrument*
        name of the instrument
    *radiation* (xray or neutron)
        source radiation type
    *T* (degrees)
        sample angle
    *slits* (mm or mm,mm)
        slit 1 and slit 2 openings
    *d_s1*, *d_s2* (mm)
        distance from sample to pre-sample slits 1 and 2; post-sample
        slits are ignored
    *wavelength* (Angstrom,Angstrom)
        wavelength range for the measurement
    *dLoL*
        constant relative wavelength dispersion; wavelength range and
        dispersion together determine the bins
    *sample_width* (mm)
        width of sample; at low angle with tiny samples, stray neutrons
        miss the sample and are not reflected onto the detector, so the
        sample itself acts as a slit, therefore the width of the sample
        may be needed to compute the resolution correctly
    *sample_broadening* (degrees FWHM)
        amount of angular divergence (+) or focusing (-) introduced by
        the sample; this is caused by sample warp, and may be read off
        of the rocking curve by subtracting (s1+s2)/2/(d_s1-d_s2) from
        the FWHM width of the rocking curve

Monochromatic measurements have these additional or modified attributes::

    *instrument*
        name of the instrument
    *radiation* (xray or neutron)
        source radiation type
    *d_s1*, *d_s2* (mm)
        distance from sample to pre-sample slits 1 and 2; post-sample
        slits are ignored
    *wavelength* (Angstrom)
        wavelength of the instrument
    *dLoL*
        constant relative wavelength dispersion; wavelength range and
        dispersion together determine the bins
    *Tlo*, *Thi* (degrees)
        range of opening slits, or inf if none
    *slits_at_Tlo* (mm)
        slit 1 and slit 2 openings at Tlo; this can be a scalar if both
        slits are open by the same amount, otherwise it is a pair (s1,s2)
    *slits_below*, *slits_above*
        slit 1 and slit 2 openings below Tlo and above Thi; again, these
        can be scalar if slit 1 and slit 2 are the same, otherwise they
        are each a pair (s1,s2)
    *sample_width* (mm)
        width of sample; at low angle with tiny samples, stray neutrons
        miss the sample and are not reflected onto the detector, so the
        sample itself acts as a slit, therefore the width of the sample
        may be needed to compute the resolution correctly
    *sample_broadening* (degrees FWHM)
        amount of angular divergence (+) or focusing (-) introduced by
        the sample; this is caused by sample warp, and may be read off
        of the rocking curve by subtracting (s1+s2)/2/(d_s1-d_s2) from
        the FWHM width of the rocking curve

These parameters should be available in the reduced data file, or they
can be found in the raw NeXus file.

GUI Usage
=========

Graphical user interfaces follow different usage patterns from scripts.
Here the emphasis will be on selecting a data set to process, displaying
its default metadata and allowing the user to override it.

File loading should follow the pattern established in reflectometry
reduction, with an extension registry and a fallback scheme whereby
files can be checked in a predefined order.  If the file cannot be
loaded, then the next loader is tried.  This should be extended with
the concept of a magic signature such as those used by graphics and
sound file applications: preread the first block and run it through
the signature check before trying to load it.  For unrecognized extensions,
all loaders can be tried.

The file loader should return an instrument instance with metadata
initialized from the file header.  This metadata can be displayed
to the user along with a plot of the data and the resolution.  When
metadata values are changed, the resolution can be recomputed and the
display updated.  When the data is accepted, the final resolution
calculation can be performed.

Calculations
============

Resolution in Q is computed from uncertainty in wavelength L and angle T
using propogation of errors::

    dQ**2 = (df/dL)**2 dL**2 + (df/dT)**2 dT**2

where::

    f(L,T) = 4 pi sin(T)/L
    df/dL = -4 pi sin(T)/L**2 = -Q/L
    df/dT = 4 pi cos(T)/L = (4 pi sin(T) / L) / (sin(T)/cos(T)) = Q/tan(T)

yielding the traditional form::

    (dQ/Q)**2 = (dL/L)**2 + (dT/tan(T))**2

Computationally, 1/tan(T) is infinity at T=0, so it is better to use the
direct calculation::

    dQ = (4 pi / L) sqrt( sin(T)**2 (dL/L)**2 + cos(T)**2 dT**2 )


Wavelength dispersion dL/L is usually constant (e.g., for AND/R it is 2%
FWHM), but it can vary on time-of-flight instruments depending on how the
data is binned.

Angular divergence dT comes primarily from the slit geometry, but can have
broadening or focusing due to a warped sample.  The slit contribution is
dT = (s1+s2)/(2d) FWHM  where s1,s2 are slit openings and d is the distance
between slits.  For tiny samples, the sample itself can act as a slit.
If s_sample = sin(T)*w is smaller than s2 for some T, then use
dT = (s1+s_sample)/(2(d+d_sample)) instead.

The sample broadening can be read off a rocking curve as  w - (s1+s2)/(2d)
where w is the measured FWHM of the peak. This constant should be added to
the computed dT for all angles and slit geometries.  You will not
usually have this information on hand, but you can leave space for users
to enter it if it is available.

FWHM can be converted to 1-sigma resolution using the scale factor of
1/sqrt(8 * log(2))

For opening slits, dT/T is held constant, so if you know s and To at the
start of the opening slits region you can compute dT/To, and later scale
that to your particular T::

    dT(Q) = dT/To * T(Q)

Because d is fixed, that means s1(T) = s1(To) * T/To and s2(T) = s2(To) * T/To

"""

# TODO: the resolution calculator should not be responsible for loading
# the data; maybe do it as a mixin?

import numpy
from numpy import pi, inf, sqrt, log, degrees, radians, cos, sin, tan
from numpy import arcsin as asin, ceil
from numpy import ones_like, arange, isscalar, asarray
from util import TL2Q, QL2T, dTdL2dQ, dQdT2dLoL, FWHM2sigma, sigma2FWHM

class Resolution:
    """
    Reflectometry resolution object.

    *T*, *dT*   (degrees) angle and FWHM divergence
    *L*, *dL*   (Angstroms) wavelength and FWHM dispersion
    *Q*, *dQ*   (inv Angstroms) calculated Q and 1-sigma resolution
    """
    def __init__(self, T, dT, L, dL, radiation="neutron"):
        self.T, self.dT = T, dT
        self.L, self.dL = L, dL
        self.radiation = radiation
    def _Q(self):
        return TL2Q(self.T,self.L)
    def _dQ(self):
        return dTdL2dQ(self.T,self.dT,self.L,self.dL)
    Q,dQ = property(_Q), property(_dQ)
    def probe(self, data=(None,None)):
        """
        Return a reflectometry measurement object of the given resolution.
        """
        from .probe import NeutronProbe, XrayProbe
        if self.radiation == 'neutron':
            return NeutronProbe(T=self.T, dT=self.dT,
                                L=self.L, dL=self.dL,
                                data=data)
        else:
            return XrayProbe(T=self.T, dT=self.dT,
                             L=self.L, dL=self.dL,
                             data=data)

class Monochromatic:
    """
    Resolution calculator for scanning reflectometers.
    """
    instrument = "monochromatic"
    radiation = "unknown"
    # Required attributes
    wavelength = None
    dLoL = None
    d_s1 = None
    d_s2 = None
    slits_at_Tlo = None
    # Optional attributes
    Tlo= 0
    Thi= inf
    slits_below = None
    slits_above = None
    sample_width = 1e10
    sample_broadening = 0

    def __init__(self, **kw):
        for k,v in kw.items():
            if not hasattr(self, k):
                raise TypeError("unexpected keyword argument '%s'"%k)
            setattr(self, k, v)

    def load(self, filename, **kw):
        """
        Load the data, returning the associated probe.  This probe will
        contain Q, angle, wavelength, measured reflectivity and the
        associated uncertainties.

        You can override instrument parameters using key=value.  In
        particular, slit settings *slits_at_Tlo*, *Tlo*, *Thi*,
        and *slits_below*, and *slits_above* are used to define the
        angular divergence.
        """
        # Load the data
        data = numpy.loadtxt(filename).T
        if data.shape[0] == 2:
            Q,R = data
            dR = None
        elif data.shape[0] > 2:
            Q,R,dR = data[:3]
            # ignore extra columns like dQ or L
        resolution = self.resolution(Q=Q, **kw)
        return resolution.probe(data=(R,dR))

    def simulate(self, T=None, Q=None, **kw):
        """
        Simulate the probe for a measurement.

        Select the *Q* values or the angles *T* for the measurement,
        but not both.

        Returns a probe with Q, angle, wavelength and the
        associated uncertainties, but not any data.

        You can override instrument parameters using key=value.  In
        particular, slit settings *slits_at_Tlo*, *Tlo*, *Thi*,
        and *slits_below*, and *slits_above* are used to define the
        angular divergence.
        """
        if (Q is None) == (T is None):
            raise ValueError("requires either Q or angle T")
        if Q is None: # Compute Q from angle T and wavelength L
            L = kw.get('wavelength',self.wavelength)
            Q = TL2Q(T,L)
        resolution = self.resolution(Q=numpy.asarray(Q), **kw)
        return resolution.probe()

    def calc_slits(self, T, **kw):
        """
        Determines slit openings from measurement pattern.

        *Tlo*,*Thi*      angle range over which slits are opening
        *slits_at_Tlo*   openings at the start of the range
        *slits_below*, *slits_above*   openings below and above the range
        """
        Tlo = kw.get('Tlo',self.Tlo)
        Thi = kw.get('Thi',self.Thi)
        slits_at_Tlo = kw.get('slits_at_Tlo',self.slits_at_Tlo)
        slits_below = kw.get('slits_below',self.slits_below)
        slits_above = kw.get('slits_above',self.slits_above)
        slits = opening_slits(T=T, slits_at_Tlo=slits_at_Tlo,
                              Tlo=Tlo, Thi=Thi,
                              slits_below=slits_below,
                              slits_above=slits_above)
        return slits

    def calc_dT(self, T, slits, **kw):
        """
        Compute the FWHM angular divergence in radians

        *d_s1*, *d_s2*  slit distances
        *sample_width*  size of sample
        *sample_broadening* resolution changes from sample warping
        """
        d_s1 = kw.get('d_s1',self.d_s1)
        d_s2 = kw.get('d_s2',self.d_s2)
        sample_width = kw.get('sample_width',self.sample_width)
        sample_broadening = kw.get('sample_broadening',self.sample_broadening)
        dT = divergence(T=T, slits=slits, distance=(d_s1,d_s2),
                        sample_width=sample_width,
                        sample_broadening=sample_broadening)

        return dT

    def resolution(self, Q, **kw):
        """
        Return the resolution for a given Q.

        Resolution is an object with fields T, dT, L, dL, Q, dQ
        """
        L = kw.get('L',self.wavelength)
        dL = L*kw.get('dLoL',self.dLoL)
        T = QL2T(Q=asarray(Q),L=L)
        slits = self.calc_slits(T, **kw)
        dT = self.calc_dT(T, slits, **kw)
        radiation = kw.get('radiation',self.radiation)

        return Resolution(T=T,dT=dT,L=L,dL=dL,radiation=radiation)

    def __str__(self):
        msg = """\
== Instrument %(name)s ==
radiation = %(radiation)s at %(L)g Angstrom with %(dLpercent)g%% resolution
slit distances = %(d_s1)g mm and %(d_s2)g mm
fixed region below %(Tlo)g and above %(Thi)g degrees
slit openings at Tlo are %(slits_at_Tlo)s mm
sample width = %(sample_width)g mm
sample broadening = %(sample_broadening)g degrees
""" % dict(name=self.instrument, L=self.wavelength, dLpercent=self.dLoL*100,
           d_s1=self.d_s1, d_s2=self.d_s2,
           sample_width=self.sample_width,
           sample_broadening=self.sample_broadening,
           Tlo=self.Tlo, Thi=self.Thi,
           slits_at_Tlo=str(self.slits_at_Tlo), radiation=self.radiation,
           )
        return msg

    @classmethod
    def defaults(cls):
        """
        Return default instrument properties as a printable string.
        """
        msg = """\
== Instrument class %(name)s ==
radiation = %(radiation)s at %(L)g Angstrom with %(dLpercent)g%% resolution
slit distances = %(d_s1)g mm and %(d_s2)g mm
""" % dict(name=cls.instrument, L=cls.wavelength, dLpercent=cls.dLoL*100,
           d_s1=cls.d_s1, d_s2=cls.d_s2,
           radiation=cls.radiation,
           )
        return msg

class Polychromatic:
    """
    Resolution calculator for multi-wavelength reflectometers.
    """
    instrument = "polychromatic"
    radiation = "neutron" # unless someone knows how to do TOF Xray...
    # Required attributes
    d_s1 = None
    d_s2 = None
    slits = None
    T = None
    wavelength = None
    dLoL = None # usually 0.02 for 2% FWHM
    # Optional attributes
    sample_width = 1e10
    sample_broadening = 0

    def __init__(self, **kw):
        for k,v in kw.items():
            if not hasattr(self, k):
                raise TypeError("unexpected keyword argument '%s'"%k)
            setattr(self, k, v)

    def load(self, filename, **kw):
        """
        Load the data, returning the associated probe.  This probe will
        contain Q, angle, wavelength, measured reflectivity and the
        associated uncertainties.

        You can override instrument parameters using key=value.
        In particular, slit settings *slits* and *T* define the
        angular divergence.
        """
        # Load the data
        data = numpy.loadtxt(filename).T
        Q,dQ,R,dR,L = data
        dL = binwidths(L)
        T = kw.pop('T',QL2T(Q,L))
        resolution = self.resolution(L=L, dL=dL, T=T, **kw)
        return resolution.probe(data=(R,dR))

    def simulate(self, **kw):
        """
        Simulate the probe for a measurement.

        Returns a probe with Q, angle, wavelength and the associated
        uncertainties, but not any data.

        You can override instrument parameters using key=value.
        In particular, slit settings *slits* and *T* define the
        angular divergence and *dLoL* defines the wavelength
        resolution.
        """
        low,high = kw.get('wavelength',self.wavelength)
        dLoL = kw.get('dLoL',self.dLoL)
        L = bins(low,high,dLoL)
        dL = binwidths(L)
        resolution = self.resolution(L=L, dL=dL, **kw)
        return resolution.probe()

    def calc_dT(self, T, slits, **kw):
        d_s1 = kw.get('d_s1',self.d_s1)
        d_s2 = kw.get('d_s2',self.d_s2)
        sample_width = kw.get('sample_width',self.sample_width)
        sample_broadening = kw.get('sample_broadening',self.sample_broadening)
        dT = divergence(T=T, slits=slits, distance=(d_s1,d_s2),
                        sample_width=sample_width,
                        sample_broadening=sample_broadening)

        return dT

    def resolution(self, L, dL, **kw):
        """
        Return the resolution of the measurement.  Needs *Q*, *L*, *dL*
        specified as keywords.

        Resolution is an object with fields T, dT, L, dL, Q, dQ
        """
        radiation = kw.get('radiation',self.radiation)
        T = kw.pop('T', self.T)
        slits = kw.pop('slits', self.slits)
        dT = self.calc_dT(T,slits,**kw)

        # Compute the FWHM angular divergence in radians
        # Return the resolution
        return Resolution(T=T,dT=dT,L=L,dL=dL,radiation=radiation)

    def __str__(self):
        msg = """\
== Instrument %(name)s ==
radiation = %(radiation)s in %(L_min)g to %(L_max)g Angstrom with %(dLpercent)g%% resolution
slit distances = %(d_s1)g mm and %(d_s2)g mm
slit openings = %(slits)s mm
sample width = %(sample_width)g mm
sample broadening = %(sample_broadening)g degrees FWHM
""" % dict(name=self.instrument,
           L_min=self.wavelength[0], L_max=self.wavelength[1],
           dLpercent=self.dLoL*100,
           d_s1=self.d_s1, d_s2=self.d_s2, slits = str(self.slits),
           sample_width=self.sample_width,
           sample_broadening=self.sample_broadening,
           radiation=self.radiation,
           )
        return msg

    @classmethod
    def defaults(cls):
        """
        Return default instrument properties as a printable string.
        """
        msg = """\
== Instrument class %(name)s ==
radiation = %(radiation)s in %(L_min)g to %(L_max)g Angstrom with %(dLpercent)g%% resolution
slit distances = %(d_s1)g mm and %(d_s2)g mm
""" % dict(name=cls.instrument,
           L_min=cls.wavelength[0], L_max=cls.wavelength[1],
           dLpercent=cls.dLoL*100,
           d_s1=cls.d_s1, d_s2=cls.d_s2,
           radiation=cls.radiation,
           )
        return msg

def bins(low, high, dLoL):
    """
    Return bin centers from low to high perserving a fixed resolution.

    *low*,*high* are the minimum and maximum wavelength.
    *dLoL* is the desired resolution FWHM dL/L for the bins.
    """
    step = 1 + dLoL;
    n = ceil(log(high/low)/log(step))
    edges = low*step**arange(n+1)
    L = (edges[:-1]+edges[1:])/2
    return L

def binwidths(L):
    """
    Construct dL assuming that L represents the bin centers of a
    measured TOF data set, and dL is the bin width.

    The bins L are assumed to be spaced logarithmically with edges::

        E[0] = min wavelength
        E[i+1] = E[i] + dLoL*E[i]

    and centers::

        L[i] = (E[i]+E[i+1])/2
             = (E[i] + E[i]*(1+dLoL))/2
             = E[i]*(2 + dLoL)/2

    so::

        L[i+1]/L[i] = E[i+1]/E[i] = (1+dLoL)
        dL[i] = E[i+1]-E[i] = (1+dLoL)*E[i]-E[i]
              = dLoL*E[i] = 2*dLoL/(2+dLoL)*L[i]
    """
    if L[1] > L[0]:
        dLoL = L[1]/L[0] - 1
    else:
        dLoL = L[0]/L[1] - 1
    dL = 2*dLoL/(2+dLoL)*L
    return dL


def divergence(T=None, slits=None, distance=None,
               sample_width=1e10, sample_broadening=0):
    """
    Calculate divergence due to slit and sample geometry.

    Returns FWHM divergence in degrees.

    *T*            (degrees) incident angles
    *slits*        (mm) s1,s2 slit openings for slit 1 and slit 2
    *distance*     (mm) d1,d2 distance from sample to slit 1 and slit 2
    *sample_width* (mm) w, width of the sample
    *sample_broadening* (degrees FWHM) additional divergence caused by sample

    Uses the following formula::

        p = w * sin(radians(T))
        dT = / (s1+s2) / 2 (d1-d2)   if p >= s2
             \ (s1+p) / 2 d1         otherwise
        dT = dT + sample_broadening

    where p is the projection of the sample into the beam.

    *sample_broadening* can be estimated from W, the FWHM of a rocking curve::

        sample_broadening = W - (s1+s2) / 2(d1-d2)

    Note: default sample width is large but not infinite so that at T=0,
    sin(0)*sample_width returns 0 rather than NaN.
    """
    # TODO: check that the formula is correct for T=0 => dT = s1 / 2 d1
    # TODO: add sample_offset and compute full footprint
    s1,s2 = slits
    d1,d2 = distance

    # Compute FWHM angular divergence dT from the slits in radians
    dT = (s1+s2)/2/(d1-d2)

    # For small samples, use the sample projection instead.
    sample_s = sample_width * sin(radians(T))
    if isscalar(sample_s):
        if sample_s < s2: dT = (s1+sample_s)/(2*d1)
    else:
        idx = sample_s < s2
        #print s1,s2,d1,d2,T,dT,sample_s
        s1 = ones_like(sample_s)*s1
        dT = ones_like(sample_s)*dT
        dT[idx] = (s1[idx] + sample_s[idx])/(2*d1)

    return dT + sample_broadening

def opening_slits(T=None,slits_at_Tlo=None,Tlo=None,Thi=None,
                  slits_below=None, slits_above=None):
    """
    Compute the slit openings for the standard scanning reflectometer
    fixed-opening-fixed geometry.

    Slits are assumed to be fixed below angle *Tlo* and above angle *Thi*,
    and opening at a constant dT/T between them.

    Slit openings are recorded at *Tlo* as a tuple (s1,s2) or constant s=s1=s2.
    *Tlo* is optional for completely fixed slits.  *Thi* is optional if there
    is no top limit to the fixed slits.

    *slits_below* are the slits at *T* < *Tlo*.
    *slits_above* are the slits at *T* > *Thi*.
    """

    # Slits at T<Tlo
    if slits_below is None:
        slits_below = slits_at_Tlo
    try:
        b1,b2 = slits_below
    except TypeError:
        b1=b2 = slits_below
    s1 = ones_like(T) * b1
    s2 = ones_like(T) * b2

    # Slits at Tlo<=T<=Thi
    if Tlo != None:
        try:
            m1,m2 = slits_at_Tlo
        except TypeError:
            m1=m2 = slits_at_Tlo
        idx = (abs(T) >= Tlo) & (abs(T) <= Thi)
        s1[idx] = m1 * T[idx]/Tlo
        s2[idx] = m2 * T[idx]/Tlo

    # Slits at T > Thi
    if Thi != None:
        if slits_above is None:
            slits_above = m1 * Thi/Tlo, m2 * Thi/Tlo
        try:
            t1,t2 = slits_above
        except TypeError:
            t1=t2 = slits_above
        idx = abs(T) > Thi
        s1[idx] = t1
        s2[idx] = t2

    return s1,s2


'''
def resolution(Q=None,s=None,d=None,L=None,dLoL=None,Tlo=None,Thi=None,
               s_below=None, s_above=None,
               broadening=0, sample_width=1e10, sample_distance=0):
    """
    Compute the resolution for Q on scanning reflectometers.

    broadening is the sample warp contribution to angular divergence, as
    measured by a rocking curve.  The value should be w - (s1+s2)/(2*d)
    where w is the full-width at half maximum of the rocking curve.

    For itty-bitty samples, provide a sample width w and sample distance ds
    from slit 2 to the sample.  If s_sample = sin(T)*w is smaller than s2
    for some T, then that will be used for the calculation of dT instead.

    """
    T = QL2T(Q=Q,L=L)
    slits = opening_slits(T=T, s=s, Tlo=Tlo, Thi=Thi)
    dT = divergence(T=T,slits=slits, sample_width=sample_width,
                    sample_distance=sample_distance) + broadening
    Q,dQ = Qresolution(L, dLoL*L, T, dT)
    return FWHM2sigma(dQ)

def demo():
    import pylab
    from numpy import linspace, exp, real, conj, sin, radians
    # Values from volfrac example in garefl
    T = linspace(0,9,140)
    Q = 4*pi*sin(radians(T))/5.0042
    dQ = resolution(Q,s=0.21,Tlo=0.35,d=1890.,L=5.0042,dLoL=0.009)
    #pylab.plot(Q,dQ)

    # Fresnel reflectivity for silicon
    rho,sigma=2.07,5
    kz=Q/2
    f = sqrt(kz**2 - 4*pi*rho*1e-6 + 0j)
    r = (kz-f)/(kz+f)*exp(-2*sigma**2*kz*f)
    r[abs(kz)<1e-10] = -1
    R = real(r*conj(r))
    pylab.errorbar(Q,R,xerr=dQ,fmt=',r',capsize=0)
    pylab.grid(True)
    pylab.semilogy(Q,R,',b')

    pylab.show()

def demo2():
    import numpy,pylab
    Q,R,dR = numpy.loadtxt('ga128.refl.mce').T
    dQ = resolution(Q, s=0.154, Tlo=0.36, d=1500., L=4.75, dLoL=0.02)
    pylab.errorbar(Q,R,xerr=dQ,yerr=dR,fmt=',r',capsize=0)
    pylab.grid(True)
    pylab.semilogy(Q,R,',b')
    pylab.show()



if __name__ == "__main__":
    demo2()
'''