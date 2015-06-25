When implementing a new calculator in OpenQuake Engine, there are some general guidelines to follow with respect to how the work should be broken up and structured.

First, we have to understand:

* What are the inputs?
* What are the outputs?

With that in mind, here is generally how we break up the work packages when implementing a new calculator:

1. config file
  - example input config file for the new calculator
  - config file validation
  - DB schema updates, for storing config parameters
* input models
  - DB schema updates for storing input models
  - XML schema updates (if any)
  - new XML parsers (or updates to existing parsers) for reading input models
* outputs
  - DB schema updates, for storing outputs
  - new or updated XML schema for export results
  - XML serializers
  - export functionality, from DB to XML
* core calculator & task code
* post-processing on "core" calculation results

We do our bug tracking in [Launchpad](https://launchpad.net/openquake), so we typically open a 'bug' for each of the numbered items above. For each bug, we try to break up the work into even smaller pieces by submitting separate pull requests for individual components. (See the section titled **Small Branches** in our [development guidelines](https://github.com/gem/oq-engine/wiki/Development-Philosophy-and-Coding-Guidelines).) Also, a feature will often require changes to multiple projects. In the case of a new calculation output, for example, changes will need to be made to [NRML](https://github.com/gem/oq-nrmllib) as well as [oq-engine](https://github.com/gem/oq-engine).

In some cases, not all of these work packages will be necessary to implement a new calculator. Often the required DB schema will already be in place, XML schema and serializers for the desired results will already exist, etc.