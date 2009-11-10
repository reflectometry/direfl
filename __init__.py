# This program is public domain
# Author: Paul Kienzle
"""
Surround variation reflectometry

The surround variation reflectometry package consists of three
interacting pieces: simulatation, phase reconstruction
and phase inversion.  Before the experiment starts, you should
provide an expected profile to the simulator.  This will indicate
whether inversion is feasible for the given structure, and allow
you to determine noise sensitivity and the effects of various
substrate and surround media.  Once you are comfortable with the
parameters, you can perform your experiment by back reflectivity
through the film on a substrate, once with one surround variation
on the surface, and again with another.  This returns a real and
imaginary reflectivity for your sample as a reversed film with the
substrate material on either side.  Next you perform inversion
on the real portion of the reflection amplitude, which returns
the scattering length density profile.  This profile can then be
used to compute the expected reflectivity for the original
measurements, which if all goes well, should agree prefectly.

See :class:`core.Inversion`, :func:`core.reconstruct` and
:class:`simulate.Simulation` for details.
"""
from core import invert, reconstruct, Inversion, SurroundVariation
from simulate import Simulation
