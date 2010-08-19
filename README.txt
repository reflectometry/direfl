Release notes for DiRefl 1.0

The Direct Inversion Reflectometry (DiRefl) application generates a scattering
length density (SLD) profile of a thin film or free form sample using two
neutron scattering datasets without the need to perform a fit of the data.
DiRefl also has a simulation capability for creating datasets from a simple
model description of the sample material.

DiRefl applies phase reconstruction and direct inversion techniques to analyze
the reflectivity datasets produced by the two neutron scattering experiments
performed on a single or multi-layer sample sandwiched between incident and
substrate layers whose characteristics are known.  The only setup difference
between the runs is that the user changes the material of one of the
surrounding layers.  Output from DiRefl is in the form of a SLD profile graph
and other supporting plots that can be saved or printed.  In addition, the user
can load, edit, and save model information, load reflectometry datasets, and
adjust several parameters that affect the qualitative results of the analysis.

The following illustrates typical usage of the program.  In preparation for
conducting the actual experiments, you are encouraged to utilize DiRefl's
simulation capability.  This is accomplished by providing a model description
of your sample, entering simulation parameters, and generating simulated
datasets as input to the phase reconstruction and direct inversion operations.
The resulting profile will indicate whether inversion is feasible for the given
structure, and allow you to determine noise sensitivity and the effects of
various substrate and surround media.  Once you are comfortable with the
parameters, you perform both of your neutron scattering experiments by back
reflectivity through the substrate side of the film, where one of the surround
materials is changed between runs.  This generates two datasets each containing
a real and an imaginary reflectivity for your sample as a reversed film with
the substrate material on either side.  Finally, you invert the real portion
of the reflection amplitude.  This returns the SLD profile of the sample that
the program uses to compute the expected reflectivity for the original
measurements.  If all goes well, the expected versus measured reflectivity
should match.

Visit http://www.reflectometry.org/danse/packages.html to download the latest
version of DiRefl and associated documentation.

DiRefl was developed jointly by the National Institute of Standards and
Technology (NIST) and the University of Maryland (UMD) as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE) project
funded by the US National Science Foundation under grant DMR-0520547.
