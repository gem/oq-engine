One of the goals of GEM is to implement a standard format for data exchange for Hazard and Risk. GEM inherited shaml from what was developed during GEM1 but never went through a "formal" review process. In order to meet the objectives it has been determined that the NRML schema be developed in order to encompass a wide variety of Risk and Hazard data formats. 

[[Notes | http://manage.gempad.globalquakemodel.org/30]] 

## Assumptions
* That an xml schema is the appropriate data exchange format for the project.
* The current xml schema does not fulfill the charter.

## Design

A coordinated effort will be made to review using rietveld and collate commentary to the ML. Then, apply proposed (consensus) changes, and update all relevant xml, xml schemas and parsers.

## User stories:
* Add serialization method to shaml codec.
* Extend shaML schema for Loss and Loss Ratio Curves.
* Serialize Hazard Curves from memcache to shaML.
* Rename shaML.
* Extend shaML to support ground-motion probability mass functions.
* Review and refactor shaML schema.
* Refactor exposure and vulnerability parser to read from the new schema.
* Serialize PMFs from memcache to shaML.
* Extend shaML for ERF logic trees.
* Extend shaML for GMPE logic trees.
* Define nrML schema containing input data for deterministic ground motion field calculation.

## Suggested Implementation

To design schemas effectively it could be suggested to begin by defining high level documentation that describes each schema. From the documentation one can then develop detailed schemas. Gather the contributions, suggestions and recommendations of developers and customers. 

## Summary
The shaML refactoer to nrML is a work in progress as the requirements for implementation continue to evolve. 

## Schema
* [nrml.xsd](https://github.com/gem/oq-engine/blob/master/docs/schema/nrml.xsd)
* [nrml_common.xsd](https://github.com/gem/oq-engine/blob/master/docs/schema/nrml_common.xsd)
* [nrml_hazard.xsd](https://github.com/gem/oq-engine/blob/master/docs/schema/nrml_hazard.xsd)
* [nrml_risk.xsd](https://github.com/gem/oq-engine/blob/master/docs/schema/nrml_risk.xsd)
* [nrml_seismic.xsd](https://github.com/gem/oq-engine/blob/master/docs/schema/nrml_seismic.xsd)

## Examples
* [Some examples](https://github.com/gem/oq-engine/tree/master/docs/schema/examples)

Back to [[Blueprints|BluePrints]]
