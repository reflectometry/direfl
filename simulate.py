# This program is public domain
# Author Paul Kienzle
"""
Phase reconstruction and direct inversion simulation code.

This code is intended to be used during your experimental proposal phase to
check that you will be able to see the features of interest in your sample
if you measure it by direct inversion.
"""
#TODO: allow sample to be a full reflectivity model
#TODO: include resolution in the simulation

from __future__ import division
import numpy
from numpy import linspace, real

from core import refl, SurroundVariation, Inversion, plottitle
try:
    from reflectometry.model1d.model.calcRefl import convolve
except:
    print "WARNING: faking convolution with linear interpolation"
    def convolve(Qin,Rin,Q,dQ): 
        return numpy.interp1(Qin,Rin,Q)
import profile

# Note that for efficiency, pylab is only imported if plotting is requested.


class Simulation():
    """
    Simulate phase-reconstruction and inversion.

    Parameters::

        *sample*        structure [(rho1,d1), ..., (rhon, dn)]
        *q*, *dq*       measurement points
        *u*, *v1*, *v2* uniform and varying SLDs for surround variation
        *noise*         percentage noise in the measurement
        *seed*          random number generator seed
        *perfect_reconstruction*
                        use real(r) from free film rather than simulated
                        reflectivity
        *phase_args*    keyword arguments for reconstruction calculation
        *invert_args*   keyword arguments for inversion calculation

    The default values for the surround are set to u=Si (2.07), v1=Air (0),
    and v2=D2O (6.33).  Noise and roughness are set to 0.

    TODO: Resolution and roughness are not yet supported.
    """

    def __init__(self, sample=None, q=None, dq=None, urough=0,
                 u=2.07, v1=0, v2=6.33, noise=0, seed=None,
                 phase_args={}, invert_args={},
                 perfect_reconstruction=False):
        if numpy.isscalar(dq): 
            dq = dq*numpy.ones_like(q)
        self.q, self.dq = q, dq
        self.sample, self.urough = sample, urough
        self.u, self.v1, self.v2 = u, v1, v2
        self.noise = noise
        self.phase_args, self.invert_args = phase_args, invert_args
        self.perfect_reconstruction = perfect_reconstruction
        self.seed = seed
        self.set()

    def set(self, **kw):
        """
        Reset or adjust input parameters, generating new sample data.
        """
        for k,v in kw.items():
            setattr(self, k, v)

        # Generate pure signals.  Note that the measurements are done
        # through the substrate, so we need to reverse the sample layers
        # in the calculation of the reflectivity.
        q, u, v1, v2 = self.q, self.u, self.v1, self.v2
        urough = self.urough

        # Measuring through the substrate so use -q to generate r1,r2
        rho = [p[0] for p in self.sample]+[u]
        d = [0] + [p[1] for p in self.sample] + [0]
        sigma = [p[2] for p in self.sample]+[urough]
        r1 = refl(-q, d, [v1]+rho, sigma=sigma)
        r2 = refl(-q, d, [v2]+rho, sigma=sigma)

        # Phase reconstruction returns the phase for the reversed free film
        # relative to the substrate, so use +q reflectivity in u surround.
        rfree = refl(q, d, [u]+rho, sigma=sigma)

        self.rfree, self.r1, self.r2 = rfree, r1, r2

        # Generate noisy measurements
        R1, R2 = abs(r1)**2, abs(r2)**2
        if self.dq is not None:
            R1, R2 = [convolve(q,R,q,self.dq) for R in (R1,R2)]
        if self.noise > 0:
            self.dR1, self.dR2 = self.noise*R1, self.noise*R2
            rng = numpy.random.RandomState(seed=self.seed)
            self.R1 = rng.normal(R1, self.dR1)
            self.R2 = rng.normal(R2, self.dR2)
        else:
            self.dR1 = self.dR2 = None
            self.R1, self.R2 = R1, R2

        self.fitz = self.fitrho = None  # Clear optimize
        self.run()

    def run(self):
        """Reconstruct phase, invert and optimize profile."""
        self._reconstruct()
        self._invert()
        if 0: self._optimize()

    def slab_profile(self):
        """Generate the sample profile."""
        z, rho_u = self.invert.z, self.invert.substrate
        rhos, widths, sigmas = zip(*self.sample)
        substrate_width = self.invert.thickness - numpy.sum(widths)
        widths = numpy.hstack((0, widths, substrate_width))
        rhos = numpy.hstack((0, rhos, rho_u))

        interface_z = numpy.cumsum(widths)
        rho_idx = numpy.searchsorted(interface_z, z)
        rho = rhos[rho_idx]
        #print rho,z
        #print rhos,interface_z

        return z,rho

    def sample_profile(self):
        z,rho_u,sigma_u = self.invert.z, self.invert.substrate, self.urough
        rhos, widths, sigmas = zip(*self.sample)
        substrate_width = self.invert.thickness - numpy.sum(widths)
        widths = numpy.hstack((0, widths, substrate_width))
        rhos = numpy.hstack((0, rhos, rho_u))
        sigmas = numpy.hstack((sigmas, sigma_u))

        #rhos,widths,sigmas = rhos[::-1],widths[::-1],sigmas[::-1]
        rho = profile.build_profile(z,value=rhos,
                                    thickness=widths,roughness=sigmas)

        return z,rho


    def phase_resid(self):
        """Return normalized residual from phase reconstruction."""
        resid = (self.phase.RealR - real(self.rfree))/abs(self.rfree)
        return resid

    def plot(self):
        """Plot summary data."""
        import pylab

        pylab.rc('font', size=8)
        self.plot_measurement(221)
        self.plot_inversion(222)
        self.plot_real(223)
        #self.plot_imaginary(223)
        self.plot_profile(224)
        pylab.rcdefaults()

    def plot_measurement(self, subplot=111):
        """Plot the simulated data."""
        import pylab

        pylab.subplot(subplot)
        if self.fitz is not None:
            z,rho = self.fitz, self.fitrho
        else:
            z,rho = self.invert.z, self.invert.rho

        self.phase.plot_measurement(profile=(z,rho))

    def plot_real(self, subplot=111):
        """Plot the simulated phase and the reconstructed phase (real)."""
        import pylab

        # Plot reconstructed phase with uncertainty
        pylab.subplot(subplot)
        q,re,dre = self.phase.Q, self.phase.RealR, self.phase.dRealR
        scale = 1e4*q**2
        [h] = pylab.plot(q, scale*re, '.', hold=False, label="Measured")
        if dre is not None:
            pylab.fill_between(q, scale*(re-dre), scale*(re+dre),
                               color=h.get_color(), alpha=0.3)

        # Plot free film phase for comparison
        q_free,re_free = self.q, real(self.rfree)
        scale = 1e4*q_free**2
        pylab.plot(q_free, scale*re_free, hold=True, label="Ideal")

        pylab.legend()
        pylab.xlabel('Q (inv A)')
        pylab.ylabel('(100 q)^2 Re r')
        plottitle('Phase Reconstruction Real Part')

    def plot_imag(self, subplot=111):
        """Plot the simulated phase (imaginary part)."""
        import pylab

        pylab.subplot(subplot)
        pylab.plot(self.phase.Q, 1e4*self.phase.Q**2*self.phase.ImagR,
                   hold=True, label="Im r+")
        pylab.plot(self.phase.Q, -1e4*self.phase.Q**2*self.phase.ImagR,
                   hold=True, label="Im r-")
        pylab.legend()
        pylab.xlabel('q')
        pylab.ylabel('(100 q)^2 Im r')
        plottitle('Phase Reconstruction Imaginary')


    def plot_phase_resid(self, subplot=111):
        """Plot the reconstructed phase residual."""
        import pylab

        pylab.subplot(subplot)
        pylab.plot(self.q, self.phase_resid())
        pylab.xlabel('q')
        pylab.ylabel('(Re r - calc Re r) / |r|')
        plottitle('Phase Inversion Residual')

    def plot_profile(self, subplot=111):
        """Plot the inverted profile."""
        import pylab

        pylab.subplot(subplot)
        
        z, rho = self.sample_profile()
        [h] = pylab.plot(z, rho, hold=False)
        self.invert.plot_profile(hold=True)
        pylab.fill_between(z, numpy.zeros_like(rho), rho,
                           color=h.get_color(), alpha=0.3)
        legend = ['Original', 'Inverted']
                
        if self.fitz is not None: # plot fitted
            pylab.plot(self.fitz, self.fitrho, hold=True)
            legend.append('Fitted')

        pylab.legend(legend)

    def plot_inversion(self, subplot=111):
        """Plot the phase of the inverted profile."""
        import pylab

        pylab.subplot(subplot)
        self.invert.plot_input()

    def check_phase(self):
        """Check that the reconstructed phase is correct within noise."""
        resid = self.phase_resid()
        if (resid<1e-12).any():
            self.plot_phase_resid()
            wait("phase inversion error")
        assert (resid<1e-12).all()

    def check_inversion(self):
        """Check that the reconstructed profile matches the sample."""
        pass

    def check(self):
        """Check phase and inversion."""
        self.check_phase()
        self.check_inversion()

    def _reconstruct(self):
        """Drive phase reconstruction."""
        data1 = self.q, self.R1, self.dR1
        data2 = self.q, self.R2, self.dR2
        u, v1, v2 = self.u, self.v1, self.v2
        self.phase = SurroundVariation(data1, data2, u=u, v1=v1, v2=v2,
                                       **self.phase_args)

    def _invert(self):
        """Drive direct inversion."""
        if self.perfect_reconstruction:
            data = self.q, real(self.rfree)
        else:
            data = self.phase.Q, self.phase.RealR, self.phase.dRealR
        substrate = self.phase.u
        thickness = numpy.sum(L[1] for L in self.sample) + 50
        self.invert = Inversion(data=data, thickness=thickness,
                                substrate=substrate, **self.invert_args)
        self.invert.run()

    def _optimize(self):
        """Drive final optimization on inverted profile"""
        z,rho = self.phase.optimize(self.invert.z, self.invert.rho)
        self.fitz, self.fitrho = z,rho

    def _swfvarnexdum(self):
        """Run phase reconstruction converted from code by Majkrzak."""
        import os

        data1 = self.q, self.R1, 0*self.q
        data2 = self.q, self.R2, 0*self.q
        numpy.savetxt('qrd1.' ,numpy.array(data1).T)
        numpy.savetxt('qrd2.' ,numpy.array(data2).T)
        fid = open('varin.', 'w')
        fid.write("%d %g %g %g\n"%(len(self.q),
                                   self.u*1e-6, self.v1*1e-6, self.v2*1e-6))
        fid.close()
        os.system('swfvarnexdum')
        q, realR = numpy.loadtxt('qrreun.').T
        self.chuckr = realR


def wait(msg=None):
    """Wait for the user to acknowledge the plot."""
    import pylab
    #from matplotlib.blocking_input import BlockingInput

    if msg: print msg

    #block = BlockingInput(fig=pylab.gcf(), eventslist=('key_press_event',))
    #block(n=1, timeout=-1)
    pylab.ginput()
