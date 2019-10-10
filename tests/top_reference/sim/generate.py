import copy

from refl1d.names import *

# Call via: refl1d generate.py --store=sim --steps=0 --simulate --noise=1e-10
data = load4("sim/generate-1-refl.datA", name="data", columns="Q dQ R dR", radiation="neutron", L=4, dL=1e-9, simulation_range=numpy.linspace(0, 1, 5001))

Si = Material("Si", name="Si")
Cu = Material("Cu")
Fe = Material("Fe")

air_slab = Slab(air, 0, 0)

t1 = Slab(SLD(rho=4), 0)
t2 = Slab(SLD(rho=4), 35)
t3 = Slab(SLD(rho=4), 36)
t4 = Slab(SLD(rho=5.64), 38.35)

b = 1.5
#si_slab = Slab(SLD(rho=b), 0, 0)  # Substrateq
si_slab = Slab(SLD(rho=b), 0, 0)

cu_slab = Slab(SLD(rho=5), 50, 0)
iron_slab = Slab(SLD(rho=6, irho=0.0), 60, 5)
#cu_slab = Slab(Cu, 50, 0)
#iron_slab = Slab(Fe, 50, 0)
rec = Stack([iron_slab, cu_slab])

cu_slab = Slab(SLD(rho=5-b), 50, 0)
iron_slab = Slab(SLD(rho=6-b), 60, 5)
rec_equiv = Stack([iron_slab, cu_slab])


samples = [
    Stack([si_slab, rec, t1, air_slab]),
    Stack([si_slab, rec, t2, air_slab]),
    Stack([si_slab, rec, t3, air_slab]),
    Stack([si_slab, rec, t4, air_slab]),
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

ampl = models[4].amplitude()
numpy.savetxt("sim/reflection.dat", zip(ampl[0], ampl[1].real, -ampl[1].imag))


#exit(0)
problem = MultiFitProblem([models[0], models[1], models[2], models[3]])