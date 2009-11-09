from simulate import Simulation
from numpy import linspace

# Fake class to make it easy to turn off tests
class NoSimulation:
    def __init__(self, **kw): pass
    def check(self): pass
    def plot(self): pass

def test():
    ro = 5
    t = Simulation(q = linspace(0,0.4,200),
                   sample = ([(5,100,ro),(1,200,ro),(3,50,ro),(-1,25,ro)]),
                   u=2, urough=0, v1=0, v2=4.3, noise=0.05,
                   inversion_args=dict(showiters=False, stages=10),
                   )
    #t.check()
    # Inversion fails if the layers get too thick.
    t_ = NoSimulation(q = linspace(0,0.4,400),
                   sample = ([(3,1000),(2,200),(3,50),(-1,25)]),
                   u=4.5, v1=2, v2=-0.53, noise=0,
                   inversion_args=dict(rhopoints=128,calcpoints=4,
                                       showiters=True))
    t.plot()
    import pylab; pylab.show()

if __name__ == "__main__":
    test()
