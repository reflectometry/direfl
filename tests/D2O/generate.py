import copy

from refl1d.names import *
#from refl1d.magnetism import Magnetism

# Call via: refl1d generate.py --store=sim --steps=0 --simulate --noise=1e-10
data = load4("../top_reference/sim/generate-1-refl.datA", name="data", columns="Q dQ R dR", radiation="neutron", L=4, dL=1e-4, simulation_range=numpy.linspace(0, 1, 5001))

substrate = Slab(SLD(rho=2.07), 0, 17.74)
ox_substrate = Slab(SLD(rho=2.11), 35, 9.104)


permalloy_mag = 2.57
#permalloy = Slab(SLD(rho=9.153 + permalloy_mag), 100, 20.511)
permalloy = Slab(SLD(rho=9.153), 100, 20.511, magnetism=Magnetism(2.57))
mag_dead_layer = Slab(SLD(rho=7.345), 46, 14.336)
unknown = Slab(SLD(rho=4.5), 336, 1.238)

samples = [
    Stack([substrate, ox_substrate, permalloy, mag_dead_layer, unknown, air]),
    #Stack([substrate, ox_substrate, permalloy_d, mag_dead_layer, unknown, air]),
]

substrate.material.rho.pmp(1)

probes = [PolarizedNeutronProbe([copy.copy(data), None, None, copy.copy(data)]) for id in range(0, len(samples))]

for probe in probes:
    probe.unique_L = np.array([4])

models = [
    Experiment(probe=probes[id], sample=samples[id]) for id in range(0, len(samples))
]

problem = MultiFitProblem([models[0]])
