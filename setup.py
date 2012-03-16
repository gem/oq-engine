"""
nhlib includes modules for modeling seismic sources (point, area and fault),
earthquake ruptures, temporal (e.g. Poissonian) and magnitude occurrence
models (e.g. Gutenberg-Richter), magnitude/area scaling relationships,
ground motion and intensity prediction equations (i.e. GMPEs and IPEs).
Eventually it will offer a number of calculators for hazard curves,
stochastic event sets, ground motion fields and disaggregation histograms.

nhlib aims at becoming an open and comprehensive tool for seismic hazard
analysis. The GEM Foundation (http://www.globalquakemodel.org/) supports
the development of the  library by adding the most recent methodologies
adopted by the seismological/seismic hazard communities. Comments,
suggestions and criticisms from the community are always very welcome.
"""
from setuptools import setup, find_packages


version = "0.01"
url = "http://github.com/gem/nhlib"

setup(
    name='nhlib',
    version=version,
    description="nhlib is a library for performing seismic hazard analysis",
    long_description=__doc__,
    url=url,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'numpy',
        'scipy',
        'shapely',
        'pyproj<1.9.0'
    ],
    scripts=['tests/gsim/check_gsim.py'],
    maintainer='Anton Gritsay',
    maintainer_email='anton@openquake.org',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering',
    ),
    keywords="seismic hazard",
    license="GNU AGPL v3",
    platforms=["any"]
)
