OpenGEM nrML schema
===================

Documentation
-------------

Within the GEM project it was decided to use standardized XML formats as a
system data representation for information.

The shaML format was developed during GEM1 and never went through a "formal"
review process. We would like to now begin a review/restructure process. To
design schemas effectively we would like to begin by defining high level
documentation that describes each schema. From the documentation we can then
produce detailed schemas. Please contribute by providing your input, suggestions
recommendations, ect. 

We would also like to rename the ML, in this document we are using for an 
example nrML (Natural Risk Mark up Language), please provide your ideas.

Some issues to consider:
- Should we use: Multiple Document Types, Multi Root Document Types, or 
a Universal Root?
- How should we best organize abstractions?
- Care should be taken to separate metadata and data
- Are all the types used?
- Are there ambiguous definition?
- Use of other schemas where appropriate (e.g. GML, QuakeML, etc)
- Values stored in attributes vs. values in node text
- Flexibility (e.g., too many or too few REQUIRED attributes, vs optional ones,
etc)
- How well it meets the design objectives
- Should we design in catch-all elements when we can not foresee all of the 
uses of a document type 

Bellow please find generalized outline to be sculpted. 

Outline
-------
nrML common
- GML
- config
* IMC
* VS30
* IMT (mmi, pga)
* min probability, max probability
* engine, version

nrML earthquake hazard reference
- historical catalog
- faulted earth
- stain rate model
- instrumental catalog 

nrML earthquake hazard
- source zones
- logic tree
- hazard curves
- PMF
- ground motion fields
- IPE's
- conversion EQ

nrML risk reference
- population exposure
- GDP
- exposure assets

nrML risk
- loss curves
- loss ratio curves
- venerability functions
- portfolio


Tools / Links
-------------

* 'shaML schema documentation <http://mercalli.ethz.ch/~fab/out/joshmckenty>'_

* 'XML Design Patterns Journey <http://www.xmlpatterns.com/intro5.shtml>'_

