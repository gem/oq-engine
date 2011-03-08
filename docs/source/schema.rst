OpenQuake NRML schema
=====================

Documentation
-------------

Within the GEM project it was decided to use standardized formats as a
system data representation for information.

The shaML format was developed during GEM1 and never went through a "formal"
review process. We would like to now begin a review/restructure process. To
design schemas effectively we would like to begin by defining high level
documentation that describes each schema. From the documentation we can then
develop detailed schemas. Please contribute by providing your input, suggestions
recommendations, etc. 

We would also like to rename the ML, in this document we are using for an 
example NRML (Natural hazards’ Risk Markup Language), please provide your ideas.

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
NRML common

- GML import
- config

* IMC
* VS30
* IMT (mmi, pga)
* min probability, max probability
* engine, version

NRML earthquake hazard reference

* historical catalog
* faulted earth
* strain rate model
* instrumental catalog 

NRML earthquake hazard

* source zones
* logic tree
* hazard curves
* PMF
* ground motion fields
* IPE's
* conversion EQ

NRML risk reference

* population exposure
* GDP
* exposed assets

NRML risk

* loss curves
* loss ratio curves
* vulnerability functions
* portfolio


Tools / Links
-------------

* 'XML Design Patterns Journey <http://www.xmlpatterns.com/intro5.shtml>'_

* 'W3C XML Schema: DOs and DON'Ts <http://kohsuke.org/xmlschema/XMLSchemaDOsAndDONTs.html>'_

