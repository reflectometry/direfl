"""
Wrapper which turns inversion calculation into plugin suitable for
SANSview style pluggable applications.
"""
# DataLoader: svn://danse.us/sans/trunk/DataLoader
from DataLoader import Data1D, plottable_1D
#import matcomp as archive
from direfl.api.invert import Inversion

class Computation(object):
    """
    Computes 1-D scattering length density profile using phase information
    from multiple reflectometry measurements, saving the computed results.
    """
    def __init__(self):
        # Error messages for the logs
        self.errors = []
        # Information messages for the user
        self.messages = []

    def __call__(self, data, **kw):
        """
        Computes inversion for a given dataset, defining profile z,rho,drho.

        Key parameters are *thickness*, *substrate*, *Qmin*, *Qmax*,
        *rhopoints*, *calcpoints* and *noise*.

        For details see :class:`api.invert.Inversion`.
        """
        result = Inversion(data=(data.x,data.y), **kw)
        result.run()
        self.chisq = result.chisq()
        self.z, self.rho, self.drho = result.z, result.rho, result.drho

    def get_plot_profile(self):
        """
        Plot the profile.
        """
        plottable = plottable_1D(self.z, self.rho, dy=self.drho)
        return plottable

    def get_state(self):
        """
        Store the result of the computation in a dictionary.
        """
        return dict(z=self.z, rho=self.rho, drho=self.drho)

    def set_state(self, state):
        """
        Retrieve the result of a computation from a dictionary.
        """
        self.z,self.rho,self.drho = state['z'],state['rho'],state['drho']

    def get_quality_parameters(self):
        """
        Returns the quality parameters for the last computation.
        """
        return dict(chisq=self.chisq)

    @classmethod
    def get_form(cls):
        """
        Returns the information necessary to populate a input form
        """
        return {
            'thickness': {
                'default':Inversion.thickness,
                'units':'&Aring;',
                'type':'float',
                'nullable':False,
                'help':'Film thickness',
                },
            'substrate': {
                'default':Inversion.substrate,
                'units':'&Aring;<span class="exponent">-2</span>',
                'type':'float',
                'nullable':True,
                'help':'Substrate Scattering Length Density',
                },
            'rhopoints': {
                'default':Inversion.rhopoints,
                'units':'',
                'type':'int',
                'nullable':True,
                'help':'Number of profile steps [dz=thickness/rhopoints]',
                },
            'calcpoints': {
                'default':Inversion.calcpoints,
                'units':'',
                'type':'int',
                'nullable':True,
                'help':'Number of calculation points per profile step',
                },
            'noise': {
                'default':Inversion.noise,
                'units':'',
                'type':'float',
                'nullable':True,
                'help':'Noise scaling factor',
                },
            'q_min': {
                'default':Inversion.Qmin,
                'units':'&Aring;<span class="exponent">-1</span>',
                'type':'float',
                'nullable':True,
                'help':'Minimum Q-value of the data used in the inversion',
                },
            'q_max': {
                'default':Inversion.Qmax,
                'units':'&Aring;<span class="exponent">-1</span>',
                'type':'float',
                'nullable':True,
                'help':'Maximum Q-value of the data used in the inversion',
                },
            }

def test():
    import numpy as np
    from numpy.linalg import norm
    # Need to reset the seed before internal and external computation
    # to check that the results are the same.
    np.random.seed(1)

    # Call inversion directly
    res = Inversion('wsh02_re.dat', thickness=125)
    res.run()

    # Call inversion via Computation object
    calc = Computation()
    Q, ReR = np.loadtxt('wsh02_re.dat').T
    data = Data1D(Q,ReR)
    np.random.seed(1)
    calc(data, thickness=125)
    state = calc.get_state()

    # Compare the results
    assert norm(res.z - state['z']) < 1e-15
    assert norm(res.rho - state['rho']) < 1e-15
    assert norm(res.drho - state['drho']) < 1e-15

    calc.get_plot_profile()

if __name__ == "__main__":
    test()
