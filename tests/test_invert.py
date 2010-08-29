import os
import sys

# Add a path to sys.path of the parent of this directory (i.e., 'inversion') so
# that this script can be run even if the inversion package is not installed.
# Note that relative imports of modules in a sibling directory cannot be done
# because this module is run in script mode and not in the context of a package.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

from api.simulate import Simulation
from numpy import linspace

def test():
    ## Roughness parameters (surface, sample, substrate)
    sv, s, su = 3, 5, 2
    ## Surround parameters
    u, v1, v2 = 2.1, 0, 4.5
    ## Default sample
    sample = ([5,100,s], (1,123,s), (3,47,s), [-1,25,s])
    ## Reversed normal sample
    #sample = list(reversed(sample))
    ## Thick sample
    #sample = ([3,1000,s], [2,200,s], [3,50,s], [-1,25,s])
    ## No bound states
    #sample = ([u+3,100,s], (u+1,123,s), [u+2,47,s])

    ## Bound state energy is sometimes necessary to get good results
    #bse = max(0,u-sample[-1][0])
    bse = 0

    ## Run the simulation
    sample[0][2] = sv
    inv = dict(showiters=False, monitor=None, bse=bse,
               noise=1, iters=6, stages=10, calcpoints=4, rhopoints=128)
    t = Simulation(q = linspace(0, 0.4, 150), dq=0.001, sample=sample,
                   u=u, urough=su, v1=v1, v2=v2, noise=0.08,
                   invert_args=inv, phase_args=dict(stages=100),
                   perfect_reconstruction=False)
    #t.check()
    t.plot()

    import pylab;
    pylab.show()


if __name__ == "__main__":
    test()
