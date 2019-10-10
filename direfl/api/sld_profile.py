import cmath
import numpy

from math import pi, ceil
from numpy import array, sin, cos, exp
from scipy.interpolate import interp1d

"""
    References:

    [Majkrzak2003] C. F. Majkrzak, N. F. Berk: Physica B 336 (2003) 27-38
        Phase sensitive reflectometry and the unambiguous determination
        of scattering  length density profiles
"""


def interpolate(x, fx):
    return interp1d(x, fx, bounds_error=False, fill_value=0)


def refr_idx(q, sld):
    """
    Calculates the refractive index with given SLD [\AA^{-2}] and wavevector transfer q [
    \AA^{-1}]. The units can be arbitrary choosen, but they must satisfy that sld/q**2 has
    unit [1]. The arguments should not be scaled by any constants.

    For example
        q = 0.01
        sld = 1e-6

    The refractive index is complex if q < q_c (being the critical edge) and it is
    completely real if q >= q_c.
    """
    return cmath.sqrt(1 - 16 * pi * sld / (q ** 2))

def reflection_matrix(q, sld, thickness, as_matrix=False):
    """
    Calculates a reflection matrix used for calculating the reflectivity of
    a slab of material (sld, thickness) for the wave vector transfer q.

    See C.F. Majkrzak, N. F. Berk: Physical Review B Vol. 52 Nr 15, 1995:
        Exact determination of the phase in neutron reflectometry, Equation (1)

    If as_matrix is True, a matrix 2x2 will be returned, if not, then the matrix
    indices are returned as a, b, c, d
    """
    n = refr_idx(q, sld)
    theta = 0.5 * q * n * thickness
    a, b, c, d = cos(theta), 1 / n * sin(theta), -n * sin(theta), cos(theta)

    if as_matrix:
        return array([[a, b], [c, d]])
    return a, b, c, d

class SLDProfile(object):
    def __init__(self):
        pass

    def as_matrix(self, q):
        """
        Returns the matrix coefficients in the abeles formalism.
        Returns w, x, y, z corresponding to the matrix [[w, x], [y, z]]
        """
        return 0, 0, 0, 0


class ConstantSLDProfile(SLDProfile):
    def __init__(self, sld, thickness, sigma=0):
        self._sld = float(sld)
        self._d = float(thickness)
        self._r = float(sigma)
        if self._r > 0:
            raise NotImplementedError("Roughness not implemented yet")

    def as_matrix(self, q):
        return reflection_matrix(q, self._sld, self._d)

class ConcatSLDProfile(SLDProfile):
    """
        The first element in sld_profiles is closest to the substrate
    """
    def __init__(self, sld_profiles, reverse=False):
        self._slds = sld_profiles
        self._reverse = reverse

    def as_matrix(self, q):
        m = len(self._slds) * [None]
        for i in range(0, len(self._slds)):
            a, b, c, d = self._slds[i].as_matrix(q)
            m[i] = array([[a, b], [c, d]])

        if self._reverse:
            m = list(reversed(m))

        m = numpy.linalg.multi_dot(m)
        return m[0][0], m[0][1], m[1][0], m[1][1]


class FunctionSLDProfile(SLDProfile):
    def __init__(self, function, support, dx=0.1):
        self._f = function
        self._supp = support
        self._dx = dx

        self._xspace = numpy.linspace(support[0], support[1],
                                      ceil((support[1] - support[0]) * 1 / dx))
        self._feval = [self._f(x) for x in self._xspace]
        self._m = [ConstantSLDProfile(fx, dx) for fx in self._feval]
        self._concat = ConcatSLDProfile(self._m, reverse=False)

    def as_matrix(self, q):
        return self._concat.as_matrix(q)


class SlabsSLDProfile(SLDProfile):
    def __init__(self, z, rho):
        self._z = z
        self._rho = rho

    @classmethod
    def from_sample(cls, sample, dz=0.1, dA=1e-4, probe=None):
        from refl1d.probe import NeutronProbe
        from refl1d.profile import Microslabs

        if probe is None:
            # The values T and L do not matter for 'just' building the SLD profile
            probe = NeutronProbe(T=[1.0], L=[1.0])

        slabs = Microslabs(1, dz)
        sample.render(probe, slabs)
        slabs.finalize(True, dA)
        # ignore the imaginary part, this should be zero anyway
        z, rho, irho = slabs.smooth_profile(dz)

        if any(irho >= 1e-2):
            raise RuntimeWarning("Sample contains absorptive SLD (imag >= 1e-2). "
                                 "Reconstruction techniques do not support this.")

        # refl1d likes to use SLD * 1e6
        return cls(z, rho * 1e-6)

    @classmethod
    def from_slabs(cls, thickness, sld, roughness, precision=1):
        # You should rather use the from_sample method, since this easier to
        # understand. This method here is just a kind of 'fallback'
        # if you dont wanna have the overhead of building the Stacks in refl1d
        # just to put the data in here..

        # WARNING: from_slabs and from_sample do not create the same slab profile
        # they are shifted profiles (by I'd guess 3*roughness[0])

        from refl1d.profile import build_profile

        w = thickness
        sld = sld

        # Means, the first layer is the substrate and we only have to include
        # the roughness effect. To do so, select a proper thickness (> 0) such
        # that the convolution with the gaussian kernel is sufficiently approximated
        if w[0] == 0:
            # refl1d uses 3 sigma usually
            # why 3?
            # that's 3 sigma and the gaussian smoothing is nearly zero out there
            # thus the 'substrate' layer is big enough to be approximated by this
            # ofc bigger sigma values (>= 5) are better, but they need more
            # computation
            w[0] = 3 * roughness[0]

        z = numpy.linspace(0, sum(w) + roughness[-1] * 5, int(precision * sum(w)) + 1)

        offsets = numpy.cumsum(w)
        rho = build_profile(z, offsets, roughness, sld)

        return cls(z, rho)

    def thickness(self):
        return max(self._z) - min(self._z)

    def plot_profile(self, offset=0, reverse=False):
        import pylab

        rho = self._rho

        if reverse:
            rho = list(reversed(self._rho))

        pylab.plot(self._z + offset, rho)

    def as_matrix(self, q):
        from functools import reduce
        # len(dz) = len(self._z) - 1
        dz = numpy.diff(self._z)
        m = len(dz) * [None]

        for idx in range(0, len(dz)):
            m[idx] = reflection_matrix(q, self._rho[idx], dz[idx], as_matrix=True)

        # There is still some potential here
        # Whats happening here:
        # m1 * m2 * m3 * m4 * m5 ... in a sequentially manner
        # maybe it's faster if you do something like
        # (m1 * m2) * (m3 * m4) * ...
        # and redo the grouping in the next step. this should be then O(log n)
        # compared to the seq. multiplication which is O(n)....
        # BUT: this has to be done in C code, not in a python implementation :/
        m = reduce(numpy.dot, m)
        return m[0][0], m[0][1], m[1][0], m[1][1]


class Reflectivity(object):
    def __init__(self, sld_profile, fronting, backing):
        assert isinstance(sld_profile, SLDProfile)

        self._sld = sld_profile
        self._f, self._b = fronting, backing

        # The input should be of the magnitude 1e-6 ... 1e-5
        if any(abs(array([fronting, backing])) >= 1e-1):
            raise RuntimeWarning("Given fronting/backing SLD values are too high")

    def reflection(self, q_space, as_function=True):
        r = numpy.ones(len(q_space), dtype=complex)

        for idx, q in enumerate(q_space):
            if abs(q) < 1e-10:
                continue

            # See [Majkrzak2003] equation (17)
            f, h = refr_idx(q, self._f), refr_idx(q, self._b)
            A, B, C, D = self._sld.as_matrix(q)

            r[idx] = (f * h * B + C + 1j * (f * D - h * A)) / \
                     (f * h * B - C + 1j * (f * D + h * A))

        if as_function:
            return self.to_function(r, q_space, square=False)
        else:
            return r

    @staticmethod
    def to_function(r, q_space, square=False):
        real = interpolate(q_space, r.real)
        imag = interpolate(q_space, r.imag)

        if square:
            return lambda q: real(q)**2 + imag(q)**2
        else:
            return lambda q: real(q) + 1j * imag(q)

    def reflectivity(self, q_space):
        r = self.reflection(q_space)
        return lambda q: abs(r(q)) ** 2

    def plot(self, q_space):
        import pylab
        R = self.reflectivity(q_space)
        pylab.plot(q_space, R(q_space))
        return R
