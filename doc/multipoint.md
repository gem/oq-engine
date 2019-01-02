MultiPointSources
=============================

Starting from version 2.5, the OpenQuake Engine is able to manage
MultiPointSources, i.e. collections of point sources with specific
properties. A MultiPointSource is determined by a mesh of points,
a MultiMFD magnitude-frequency-distribution and 9 other parameters:

1. tectonic region type
2. rupture mesh spacing
3. magnitude-scaling relationship
4. rupture aspect ratio
5. temporal occurrence model
6. upper seismogenic depth
7. lower seismogenic depth
8. NodalPlaneDistribution
9. HypoDepthDistribution

The MultiMFD magnitude-frequency-distribution is a collection of
regular MFD instances (one per point); in order to instantiate a
MultiMFD object you need to pass a string describing the kind of
underlying MFD ('arbitraryMFD', 'incrementalMFD',
'truncGutenbergRichterMFD' or 'YoungsCoppersmithMFD'), a float
determining the magnitude bin width and few arrays describing the
parameters of the underlying MFDs. For instance, in the case of an
'incrementalMFD', the parameters are `min_mag` and `occurRates` and
a `MultiMFD` object can be instantiated as follows::

```python
mmfd = MultiMFD('incrementalMFD',
                size=2,
                bin_width=[2.0, 2.0],
                min_mag=[4.5, 4.5],
                occurRates=[[.3, .1], [.4, .2, .1]])
```

In this example there are two points and two underlying MFDs; the
occurrence rates can be different for different MFDs: here the first
one has 2 occurrence rates while the second one has 3 occurrence
rates.

Having instantiated the `MultiMFD`, a `MultiPointSource` can be instantiated
as in this example:

```python
npd = PMF([(0.5, NodalPlane(1, 20, 3)),
          (0.5, NodalPlane(2, 2, 4))])
hd = PMF([(1, 4)])
mesh = Mesh(numpy.array([0, 1]), numpy.array([0.5, 1]))
tom = PoissonTOM(50.)
rms = 2.0
rar = 1.0
usd = 10
lsd = 20
mps = MultiPointSource('mp1', 'multi point source',
                       'Active Shallow Crust',
                        mmfd, rms, PeerMSR(), rar,
                        tom, usd, lsd, npd, hd, mesh)
```
There are two major advantages when using `MultiPointSources`:

1. the space used is a lot less than the space needed for an equivalent
   set of PointSources (less memory, less data transfer)
2. the XML serialization of a MultiPointSource is a lot more efficient (say
   10 times less disk space, and faster read/write times)
   
At computation time MultiPointSources are split into PointSources and are
indistinguishable from those. The serialization is the same as for other
source typologies (call `write_source_model(fname, [mps])` or
`nrml.to_python(fname, sourceconverter)`) and in XML a `multiPointSource`
looks like this::

```xml
            <multiPointSource
            id="mp1"
            name="multi point source"
            tectonicRegion="Stable Continental Crust"
            >
                <multiPointGeometry>
                    <gml:posList>
                        0.0 1.0 0.5 1.0
                    </gml:posList>
                    <upperSeismoDepth>
                        10.0
                    </upperSeismoDepth>
                    <lowerSeismoDepth>
                        20.0
                    </lowerSeismoDepth>
                </multiPointGeometry>
                <magScaleRel>
                    PeerMSR
                </magScaleRel>
                <ruptAspectRatio>
                    1.0
                </ruptAspectRatio>
                <multiMFD
                kind="incrementalMFD"
                size=2
                >
                    <bin_width>
                        2.0 2.0
                    </bin_width>
                    <min_mag>
                        4.5 4.5
                    </min_mag>
                    <occurRates>
                        0.10 0.05 0.40 0.20 0.10
                    </occurRates>
                    <lengths>
                        2 3
                    </lengths>
                </multiMFD>
                <nodalPlaneDist>
                    <nodalPlane dip="20.0" probability="0.5" rake="3.0" strike="1.0"/>
                    <nodalPlane dip="2.0" probability="0.5" rake="4.0" strike="2.0"/>
                </nodalPlaneDist>
                <hypoDepthDist>
                    <hypoDepth depth="14.0" probability="1.0"/>
                </hypoDepthDist>
            </multiPointSource>
```

The node `<lengths>` contains the lengths of the occurrence rates, 2 and 3
respectively in this example. This is needed since the serializer writes
the occurrence rates sequentially (in this example they are the 5 floats
`0.10 0.05 0.40 0.20 0.10`) and the information about their grouping would
be lost otherwise.

There is an optimization for the case of homogeneous parameters;
for instance in this example the `bin_width` and `min_mag` are the same
in all points; then it is possible to store these as one-element lists:

```python
mmfd = MultiMFD('incrementalMFD',
                size=2,
                bin_width=[2.0],
                min_mag=[4.5],
                occurRates=[[.3, .1], [.4, .2, .1]])
```

This saves memory and data transfer, compared to the version of the code
above.

Notice that writing `bin_width=2.0` or `min_mag=4.5` would be an error: the
parameters must be vector objects; if their length is 1 they are
threated as homogeneous vectors of size `size`. If their length is different
from 1 it must be equal to `size`, otherwise you will get an error at
instantiation time.
