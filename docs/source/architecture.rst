OpenGEM System Architecture
===========================

The toughest challenges in addressing opengem architecture are nomenclature: 

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
* Engines:
 * Risk Engine
 * Hazard Engine
 * SEI Engine
* Viewer's Interface
* Datastores (with REST interfaces)
* Job Queue
* Single-Sign-On Service layer