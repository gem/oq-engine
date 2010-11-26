OpenQuake System Architecture
=============================

The toughest challenges in addressing OpenQuake architecture are nomenclature: 

  System "input" is a combination of data, algorithms, and configuration.

Therefore, system components will be built to work in a variety of fashions:

	They will be written as python modules, which if executed from the command line, will accept command line arguments (and optionally STDIN) and return output on STDOUT.
	They will support an AMQP consumer/publisher interface, allowing them to run as daemons and consume / deliver messages.
	(An adapter may be developed that would allow AMQP->CONDOR or GLOBUS bridging, as appropriate)
	A thin REST API wrapper will be developed that will communicate async with the various components over AMQP.
	Some components will support native REST APIs, as appropriate.

Data stores will be of four types:

* Relational Data (PostGIS)
* NoSQL KVS (redis, cassandra)
* Blob store (swift, cloudfiles, etc)
* Versioned data (using git, ala gitpython http://michaeltrier.com/2008/5/8/gitpython or gitshelve http://www.newartisans.com/2008/05/using-git-as-a-versioned-data-store-in-python.html)


System components list:

* Modeller's Toolkit

 - This is a web-based GIS interface that provides real-time analysis of composite spatial data, and an integrated set of GIS editing tools to produce source zone definitions, and other required inputs to the Engines and calculators.
 
There are three "Engines", each of which is composed of multiple "calculators":

The HAZARD ENGINE is composed of the following calculators:

 - Classic PSHA, The Hazard component will need to produce earthquake rupture forecast (ERF) as it is required in order for the stochastic event set generator.
 - Stochastic Event Set Generator. The Stochastic Event Set Generator is required for the Ground Motion Fields calculator.
 
The RISK ENGINE is composed of the following calculators:

 - Classical PSHA Based Risk Assessment. The OpenQuake Risk calculator is capable of computing losses due to all the possible seismic events that might occur within a given time span using a classical PSHA-based approach. The main product from these calculations will be loss/loss ratio curves although, loss/loss ratio maps for different probabilities of exceedance as well as average loss/loss ratio maps can also be computed.
 - Probabilistic Event Based Risk Assessment. The OpenQuake Risk calculator is intended to compute probabilistic event based assessment: using set of ground motion fields (generated through stochastic event set) the risk engine is capable of computing losses per asset and/or the aggregated loss since in this approach it is possible to take into consideration the spatial correlation of the ground motion.
 - Deterministic Event Based Risk Assessment. Deterministic event-based risk assessment involves the calculation of losses (or loss ratios) for a given set of exposed assets, for a single deterministic earthquake scenario. It requires a ground-motion field (GMF), discrete vulnerability functions and exposure portfolios. The deterministic event based assessment is intended to produce loss / loss ratio maps and statistical data for a specific site.
 - Wesson et al Calculator. Wesson et all approach represents a direct method for the calculation of the annual frequency of exceedance of a certain earthquake loss. This method parallels the classic method of probabilistic seismic hazard analysis for the calculation  of the annual frequency of exceedance for earthquake ground motions. The method assumes conditional independence of the random component of ground motions and losses at different sites for each earthquake, given magnitude, distance to the sites, and so-called interevent epsilon. The main advantage of this method is that it does not require a separate set of scenario earthquakes, as do Monte Carlo-based approaches and the main drawback, is the fact that it does not take into account the spatial correlation of the ground motion (intra-event correlation)

The SOCIO-ECONOMIC IMPACT Engine is composed of the following calculators:
 - Agent based model
 - System Economics model
