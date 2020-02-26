from os.path import dirname, realpath, join as joinpath
import pylab
import numpy as np

from refl1d.names import *

from direfl.api.reference_layer import BottomReferenceVariation
from direfl.api.sld_profile import ConcatSLDProfile, ConstantSLDProfile, FunctionSLDProfile

ROOT = dirname(realpath(__file__))
def getdata(filename):
    return joinpath(ROOT, "sim", filename)

# SLD: Si: ~2.1 (2.1 is set precisely in generate.py)
#      Air: 0
var = BottomReferenceVariation(0e-6, 2.1e-6)

sld = FunctionSLDProfile(lambda x: 4e-6 if x < 15 else 5e-6, [0, 30], 15)
sld_concat = ConcatSLDProfile([ConstantSLDProfile(5.0e-6, 15), ConstantSLDProfile(5.5e-6, 35)])

var.load(getdata("generate-1-refl.datA"), sld)
var.load(getdata("generate-2-refl.datA"), sld_concat)
# var.load(getdata("generate-3-refl.datA"), ConstantSLDProfile(6.0e-6, 70))
var.run()

def load_reflection(file):
    q, real, imag = np.loadtxt(file).T
    return q, real + 1j * imag

q, r = load_reflection(getdata("reflection.dat"))

# Load the exact reflection coefficient
# exact_amplitude = np.loadtxt('sim/reflection.dat').T

pylab.plot(q, 1e4 * r.real * q ** 2)
pylab.plot(q, 1e4 * r.imag * q ** 2)

if var.number_measurements == 2:
    var.plot_r_branches()
    var.plot_r_choose(1)
    pylab.show()

    R, _, _ = var.choose(1)

if var.number_measurements > 2:
    var.plot_phase()
    pylab.show()

    R = var.R

from dinv.glm import PotentialReconstruction
from dinv.fourier import FourierTransform

fourier = FourierTransform(var.Q / 2.0, R.real, R.imag, offset=-50)
# fourier.method = fourier.cosine_transform
rec = PotentialReconstruction(250, 4, cutoff=2)
pot = rec.reconstruct(fourier)
x_space = np.linspace(0, 250, 1001)

pylab.plot(x_space, [pot(x) for x in x_space])
pylab.show()
