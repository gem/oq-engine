* **engine**

  The term "engine" refers to the OpenQuake Engine, the piece of software which is responsible for reading inputs, distributing calculations, and collecting outputs.

* **calculation**

  A unique set of input files for which we attempt to produce results. Input files include an INI-style config file (containing various calculation parameters) and various XML files. The structure of these XML files is defined by our XML specification: NRML. The quantity, type, and content of these XML files will vary depending on the calculation mode.

  The terms calculation and job are often used synonymously, but it is important to understand the distinction.

* **job**

  The runtime “thing” which represents an attempt to complete a calculation. The job contains various pieces of information which are relevant while a calculation is in progress, including:
	- status (i.e., “Is it running?”, as well as the calculation phase)
	- logging level
	- the user who initiated/owns this job
	- engine process IDs

  If in the future calculation resumability is supported, there could be more than 1 job associated with a calculation.

* **calculator**

  A Python class which can implement various methods associated with each calculation phase. In order of execution, the phases are:

	- pre_execute
	- execute (this is the only required method)
	- post_execute
	- post_process
	- export
	- clean_up

  Each calculation mode has its own calculator class defined, although many common functionalities are shared between calculators. This common functionality is abstracted into common base classes and plain functions.

* **task**

  A task is a function which is passed a subset of the overall work to be completed for a calculation. Tasks are intended to be executed in asynchronous/parallel fashion and are independent from each other.

  Breaking a calculation into tasks in this manner allows the OpenQuake Engine to distribute a calculation workload among many worker machines.

* **control node**

  The machine from which the user initiates a calculation. The control is responsible for running code which processes user input, initializes a calculation, distributes work, and manages/monitors the calculation until completion.

  By convention, the machine used as the control node does not process tasks. The control node is also typically the machine which runs vital server processes, such as RabbitMQ, and PostgreSQL/PostGIS.

* **worker process**

  A process which is dedicated to task execution.

* **worker machine**

  A machine dedicated to run worker processes.

  The concepts of “worker machines” and “worker processes” are often referred to synonymously (as “workers”, for short). Technically, there can be many worker processes running on a single worker machine. The number of worker processes per machine is typically equal to the number of CPU cores available.

* **NRML**

  Natural hazards’ Risk Markup Language (NRML) is the officially supported input/output format for calculation artifacts. NRML includes a custom set of XML schema definitions, as well as a number XML parsers and serializers for reading and writing NRML artifacts.

* **OpenQuake Hazard Library**

  The OpenQuake Hazard Library (`openquake.hazardlib`) is the Python library the OpenQuake team has developed to function as the core scientific library behind the OpenQuake Engine for Seismic Hazard.

* **OpenQuake Risk Library**

  The OpenQuake Risk Library (`openquake.risklib`) is the Python library the OpenQuake team has developed to function as the core scientific library behind the OpenQuake Engine for Seismic Risk.
