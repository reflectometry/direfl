# This program is public domain
# Author Paul Kienzle
"""
Phase reconstruction and direct inversion simulation code.

Use this as part of you experiment proposal to check that you will be
able to see the features of interest in your sample if you measure it
by direct inversion.
"""
#TODO: allow sample to be a full reflectivity model
#TODO: include resolution in the simulation
from __future__ import division
import numpy
from numpy import linspace, real

from core import refl, SurroundVariation, Inversion

class Simulation:
    """
    Simulate phase-reconstruction and inversion.

    Parameters::

      *sample*          structure [(rho1,d1), ..., (rhon, dn)]
      *q*, *dq*         measurement points
      *u*, *v1*, *v2*   uniform and varying SLDs for surround variation
      *noise*           percentage noise in the measurement
      *roughness*       interface roughness

    The defaults are set to u=Si (2.1), v1=Air (0) and v2=D2O (6.33).
    Noise and roughness are set to 0.

    TODO: Resolution and roughness are not yet supported.
    """
    def __init__(self, sample=None, roughness=0, q=None, dq=None,
                 u=2.1, v1=0, v2=6.33, noise=0, inversion_args={}):
        self.q, self.dq = q,dq
        self.sample, self.roughness = sample, roughness
        self.u, self.v1, self.v2 = u, v1, v2
        self.noise = noise
        self.inversion_args = inversion_args
        self.set()

    def set(self, **kw):
        """
        Reset or adjust input parameters, generating new sample data.
        """
        for k,v in kw.items():
            setattr(self,k,v)

        # Generate pure signals.  Note that the measurements are done
        # through the substrate, so we need to reverse the sample layers
        # in the calculation of the reflectivity.
        q,u,v1,v2 = self.q,self.u,self.v1,self.v2

        rho = [p[0] for p in self.sample]
        d = [0] + [p[1] for p in self.sample] + [0]
        r1 = refl(q,d,[u]+rho+[v1])
        r2 = refl(q,d,[u]+rho+[v2])

        revshift_rho = [p[0]-u for p in reversed(self.sample)]
        revd = [0] + [p[1] for p in reversed(self.sample)] + [0]
        rfree = refl(q,revd,[0]+revshift_rho+[0])

        self.rfree,self.r1,self.r2 = rfree,r1,r2

        # Generate noisy measurements
        R1, R2 = abs(r1)**2, abs(r2)**2
        if self.noise:
            self.dR1, self.dR2 = self.noise*R1, self.noise*R2
            self.R1 = numpy.random.normal(R1,self.dR1)
            self.R2 = numpy.random.normal(R2,self.dR2)
        else:
            self.dR1 = self.dR2 = None
            self.R1, self.R2 = R1, R2

        self._reconstruct()
        self._invert(**self.inversion_args)

    def sample_profile(self):
        """
        Generate the sample profile.
        """
        z,rho_u = self.invert.z, self.invert.substrate
        rhos, widths = zip(*self.sample)
        vacuum_width = self.invert.thickness - numpy.sum(widths)
        widths = numpy.hstack((vacuum_width, widths))
        rhos = numpy.hstack((0,rhos,rho_u))
        interface_z = numpy.cumsum(widths)
        rho_idx = numpy.searchsorted(interface_z, z)
        rho = rhos[rho_idx]
        #print rho,z
        #print rhos,interface_z
        return z,rho

    def phase_resid(self):
        """Return normalized residual from phase reconstruction"""
        resid = (self.phase.RealR - real(self.rfree))/abs(self.rfree)
        return resid

    def plot(self):
        """Summary plot"""
        import pylab
        pylab.rc('font',size=8)
        self.plot_measurement(221)
        self.plot_real(223)
        self.plot_inversion(222)
        self.plot_profile(224)
        pylab.rcdefaults()

    def plot_measurement(self, subplot=111):
        """Plot the simulated data"""
        import pylab
        pylab.subplot(subplot)
        if self.noise != 0:
            pylab.errorbar(self.q,self.R1,yerr=self.dR1,
                           hold=False,label="v1")
            pylab.errorbar(self.q,self.R2,yerr=self.dR2,
                           hold=True,label="v2")
            pylab.yscale('log')
        else:
            pylab.semilogy(self.q,self.R1,'.',hold=False,label="v1")
            pylab.semilogy(self.q,self.R2,'.',hold=True,label="v2")
        pylab.legend()
        pylab.title('Measured data')
        pylab.ylabel('R')

    def plot_real(self, subplot=111):
        """Plot the simulated phase and the reconstructed phase (real)"""
        import pylab
        pylab.subplot(subplot)

        # Plot reconstructed phase with uncertainty
        q,re,dre = self.phase.Q, self.phase.RealR, self.phase.dRealR
        scale = 1e6*q**2
        [h] = pylab.plot(q, scale*re, hold=False, label="measured")
        if dre is not None:
            pylab.fill_between(q, scale*(re-dre), scale*(re+dre),
                               color=h.get_color(),alpha=0.3)

        # Plot free film phase for comparison
        q_free,re_free = self.q, real(self.rfree)
        scale = 1e6*q_free**2
        pylab.plot(q_free, scale*re_free, hold=True, label="freefilm")

        pylab.legend()
        pylab.xlabel('q')
        pylab.ylabel('10^6 q**2 * Re r')
        pylab.title('Phase reconstruction Real')

    def plot_imag(self, subplot=111):
        """Plot the simulated phase (imag)"""
        import pylab
        pylab.subplot(subplot)
        pylab.plot(self.phase.Q, 1e6*self.phase.Q**2*self.phase.ImagR,
                   hold=True, label="Im r+")
        pylab.plot(self.phase.Q, -1e6*self.phase.Q**2*self.phase.ImagR,
                   hold=True, label="Im r-")
        pylab.legend()
        pylab.xlabel('q')
        pylab.ylabel('10^6 q**2 * Im r')
        pylab.title('Phase reconstruction Imag')


    def plot_phase_resid(self, subplot=111):
        """Plot the reconstructed phase residual"""
        import pylab
        pylab.subplot(subplot)
        pylab.plot(self.q, self.phase_resid())
        pylab.xlabel('q')
        pylab.ylabel('(Re r - calc Re r) / |r|')
        pylab.title('Phase inversion residual')

    def plot_profile(self, subplot=111):
        """Plot the inverted profile"""
        import pylab
        pylab.subplot(subplot)
        self.invert.plotprofile()

        z,rho = self.sample_profile()
        [h] = pylab.plot(z,rho,hold=True)
        pylab.fill_between(z,numpy.zeros_like(rho),rho,
                           color=h.get_color(),alpha=0.3)
        pylab.legend(['inverted','original'])
        pylab.title('SLD Profile')

    def plot_inversion(self, subplot=111):
        """Plot the phase of the inverted profile"""
        import pylab
        pylab.subplot(subplot)
        self.invert.plotdata()
        pylab.title('Phase inversion')

    def check_phase(self):
        """Check that the reconstructed phase is correct within noise"""
        resid = self.phase_resid()
        if (resid<1e-12).any():
            self.plot_phase_resid(), wait("phase inversion error")
        assert (resid<1e-12).all()

    def check_inversion(self):
        """Check that the reconstructed profile matches the sample"""
        pass

    def check(self):
        """Check phase and inversion"""
        self.check_phase()
        self.check_inversion()

    def _reconstruct(self):
        """Drive phase reconstruction"""
        data1 = self.q,self.R1,self.dR1
        data2 = self.q,self.R2,self.dR2
        u,v1,v2 = self.u,self.v1,self.v2
        self.phase = SurroundVariation(data1,data2,u=u,v1=v1,v2=v2)

    def _invert(self, **kw):
        """Drive direct inversion"""
        data = self.phase.Q, self.phase.RealR #, self.phase.dRealR
        #data = self.q, real(self.rfree)
        substrate = self.phase.u
        thickness = numpy.sum(L[1] for L in self.sample) + 50
        self.invert = Inversion(data=data,thickness=thickness,
                                substrate=substrate,**kw)
        self.invert.run()

    def _swfvarnexdum(self):
        """Run phase reconstruction code by Majkrzak"""
        data1 = self.q,self.R1,0*self.q
        data2 = self.q,self.R2,0*self.q
        numpy.savetxt('qrd1.',numpy.array(data1).T)
        numpy.savetxt('qrd2.',numpy.array(data2).T)
        fid = open('varin.','w')
        fid.write("%d %g %g %g\n"%(len(self.q),
                                   self.u*1e-6,self.v1*1e-6,self.v2*1e-6))
        fid.close()
        import os
        os.system('swfvarnexdum')
        q,realR = numpy.loadtxt('qrreun.').T
        self.chuckr = realR


def wait(msg=None):
    """Wait for the user to acknowledge the plot"""
    if msg: print msg

    import pylab
    #from matplotlib.blocking_input import BlockingInput
    #block = BlockingInput(fig=pylab.gcf(), eventslist=('key_press_event',))
    #block(n=1, timeout=-1)
    pylab.ginput()

