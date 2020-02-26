import copy

from refl1d.names import *

# Call via: refl1d generate.py --store=sim --steps=0 --simulate --noise=1e-10
data = load4("sim/generate-1-refl.datA", name="data", columns="Q dQ R dR", radiation="neutron", L=5, dL=1e-8, simulation_range=numpy.linspace(0, 1, 5001))

Si = Material("Si", name="Si")
Cu = Material("Cu")
Fe = Material("Fe")

air_slab = Slab(air)

# Reference slabs
t1 = Slab(SLD(rho=4), 30)
t12 = Slab(SLD(rho=4), 15)
t22 = Slab(SLD(rho=5), 15)
t2 = Slab(SLD(rho=5.5), 35)
t3 = Slab(SLD(rho=6), 70)

si_slab = Slab(SLD(rho=2.1), 0, 0)  # Substrate

#cu_slab = Slab(Cu, 50, 0)
#iron_slab = Slab(Fe, 220, 0)

cu_slab = Slab(SLD(rho=6.4), 50, 5)
iron_slab = Slab(SLD(rho=8.1), 50, 2)
air_slab = Slab(air, 0, 0)
rec = Stack([cu_slab, iron_slab])

# We have to revert the film, so, we have to change the interfaces, too.
# Initially we have |REF| 0A |Cu| 5A |Fe| 2A |Air|
# hence, reverting yields |Air| 2A |Fe| 5A |Cu| 0A |Air|
air_slab2 = Slab(air, 0, 2)
iron_slab = Slab(SLD(rho=8.1), 50, 5)
cu_slab = Slab(SLD(rho=6.4), 50, 0)
rec_rev = Stack([iron_slab, cu_slab])


samples = [
    Stack([si_slab, t12, t22, rec, Slab(air)]),
    Stack([si_slab, t22, t2, rec, Slab(air)]),
    Stack([si_slab, t3, rec, Slab(air)]),
    Stack([air_slab2, rec_rev, Slab(air)])
]

# 'fit' anything so that it actually generates the reflectivities
t3.material.rho.pmp(1)

probes = [PolarizedNeutronProbe([copy.copy(data), None, None, None]) for id in [0, 1, 2, 3]]

for probe in probes:
    probe.unique_L = np.array([4])

models = [
    Experiment(probe=probes[id], sample=samples[id]) for id in [0, 1, 2, 3]
]

# Calculate the exact reflection coefficient (not the reflectivity!)
ampl = models[3].amplitude()
np.savetxt("sim/reflection.dat", zip(ampl[0], ampl[1].real, -ampl[1].imag))

# plot the reflectivity
problem = MultiFitProblem([models[0], models[1], models[2]])
