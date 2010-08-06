#!/usr/bin/python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
This is a demo script to show jpype running our OpenSHA hazard calculations.

It is a direct port of the code found in:
  org.opensha.gem.GEM1.calc.gemHazardMaps.NshmpSouthAmerica

Run it with:

  python demo_jpype.py

To run this you will need a jar built of openSHA with the gem code and have
it in the ./lib directory.

"""

import os

import jpype

# These are the lines to start up the the java <--> python bridge
# We add the lib directory to the jar path, it expects there to be a jar
# of the OpenSHA + gem build.
jarpath = os.path.join(os.path.abspath('.'), 'lib')
jpype.startJVM(jpype.getDefaultJVMPath(), '-Djava.ext.dirs=%s' % jarpath)

# These lines are the same as the imports in Java
GemComputeModel = jpype.JClass(
    'org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel')
GemGmpe = jpype.JClass(
    'org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe')
NshmpSouthAmericaData = jpype.JClass(
    'org.opensha.gem.GEM1.calc.gemModelData.nshmp'
    '.south_america.NshmpSouthAmericaData')
NshmpSouthAmerica = jpype.JClass(
    'org.opensha.gem.GEM1.calc.gemHazardMaps.NshmpSouthAmerica')
CalculationSettings = jpype.JClass(
    'org.opensha.gem.GEM1.commons.CalculationSettings')
CpuParams = jpype.JClass('org.opensha.gem.GEM1.util.CpuParams')
DistanceParams = jpype.JClass('org.opensha.gem.GEM1.util.DistanceParams')

# Primitive types in python will be automatically adjusted to java as per:
#   http://jpype.sourceforge.net/doc/user-guide/userguide.html#conversion
modelName = 'NshmpSouthAmerica'

latmin = -55.0
latmax = 15.0
lonmin = -85.0
lonmax = -30.0
delta = 10.0

probLevel = [0.02, 0.05, 0.1]
nproc = 1
outDir = '/tmp/gen_nshmp/'
outputHazCurve = True

# We can instantiate classes as normal
gmpeLogicTree = GemGmpe()
model = NshmpSouthAmericaData(latmin, latmax, lonmin, lonmax)
calcSet = CalculationSettings()

# We can also access members of imported classes and call methods on our
# instances of java classes.
calcSet.getOut().put(CpuParams.CPU_NUMBER.toString(), nproc)

# To access the builtin java classes and functions use jpype.java.lang
jpype.java.lang.System.out.println('Number of sources considered: %s'
                                   % model.getList().size())

# And we can pass all these complex types into a big class and it will do the
# computation :)
GemComputeModel(model.getList(),
                modelName,
                gmpeLogicTree.getGemLogicTree(),
                latmin, latmax, lonmin, lonmax, delta,
                probLevel,
                outDir,
                outputHazCurve,
                calcSet)
