One of the goal of GEM is to implement a standard format for data exchange for Risk and Hazard. GEM inherited shaml from that was developed during GEM1 but never went through a "formal" review process. In order to meet the objective it has been determined that a NRML schema be developed in order to encompass a wide variety of risk and hazard data formats. 

[[Notes | http://manage.gempad.globalquakemodel.org/30]] 

* Assumptions
    * That an xml schema is the appropriate data exchange format for the project.
    * The current xml schema does not fulfill the charter.

* Design

A coordinated effort will be made to review using rietveld and collate commentary to the ML. Then, apply proposed (consensus) changes, and update all relevant xml, xml schemas and parsers.

* Suggested Implementation

To design schemas effectively it could be suggested to begin by defining high level documentation that describes each schema. From the documentation one can then develop detailed schemas. Gather the contributions, suggestions and recommendations of developers and customers. 

* Summary
The shaML refactoer to nrML is a work in progress as the requirements for implementation continue to evolve. 


Back to [[Blueprints|BluePrints]]