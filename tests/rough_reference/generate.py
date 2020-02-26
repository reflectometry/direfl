import copy

from refl1d.names import *

# Call via: refl1d generate.py --store=sim --steps=0 --simulate --noise=1e-10
data = load4("sim/generate-1-refl.datA", name="data", columns="Q dQ R dR", radiation="neutron",
             L=4, dL=1e-9, simulation_range=np.linspace(0, 1, 5001))

Si = Material("Si", name="Si")
Cu = Material("Cu")
Fe = Material("Fe")

air_slab = Slab(air, 0, 0)

b = 1.5
# si_slab = Slab(SLD(rho=b), 0, 0)  # Substrate
si_slab = Slab(SLD(rho=b), 0, 0)
si_slab_rough = Slab(SLD(rho=b), 0, 7)

t1 = Slab(SLD(rho=4), 20, 0)
t2 = Slab(SLD(rho=4), 35, 2)
t3 = Slab(SLD(rho=4), 40, 0)
t4 = Slab(SLD(rho=5.64), 38.35, 0)
t5 = Slab(SLD(rho=2), 30)
t6 = Slab(SLD(rho=5), 30)

cu_slab = Slab(SLD(rho=5), 50, 0)
iron_slab = Slab(SLD(rho=6, irho=0.0), 60, 5)
# cu_slab = Slab(Cu, 50, 0)
# iron_slab = Slab(Fe, 50, 0)
rec = Stack([iron_slab, cu_slab])

cu_slab = Slab(SLD(rho=5 - b), 50, 5)
iron_slab = Slab(SLD(rho=6 - b), 60, 0)
rec_equiv = Stack([cu_slab, iron_slab])

samples = [
    Stack([si_slab, t1, t5, rec, air_slab]),
    Stack([si_slab, t2, t5, rec, air_slab]),
    Stack([si_slab, t3, t5, rec, air_slab]),
    Stack([si_slab, t4, t5, rec, air_slab]),
    Stack([si_slab_rough, t6, rec, air_slab]),
    Stack([Slab(SLD(rho=0), 0, 0), rec_equiv, Slab(SLD(rho=0), 0, 0)]),
]

t2.material.rho.pmp(1)
t3.material.rho.pmp(1)

probes = [PolarizedNeutronProbe([copy.copy(data), None, None, None]) for sample in samples]

for probe in probes:
    probe.unique_L = np.array([4])

models = [
    Experiment(probe=probes[id], sample=samples[id]) for id in range(0, len(samples))
]

ampl = models[5].amplitude()
numpy.savetxt("sim/reflection.dat", zip(ampl[0], ampl[1].real, -ampl[1].imag))

# exit(0)
problem = MultiFitProblem([models[idx] for idx in range(0, len(samples)-1)])
