.. _architecture-of-oq-engine:

Architecture of the OpenQuake engine
====================================

The engine is structured as a regular scientific application: we try to perform calculations as much as possible in 
memory and when it is not possible intermediate results are stored in HDF5 format. We try to work as much as possible in 
terms of arrays which are efficiently manipulated at C/Fortran speed with a stack of well established scientific 
libraries (numpy/scipy).

CPU-intensity calculations are parallelized with a custom framework (the engine is ten years old and predates frameworks 
like `dask <https://dask.org/>`_ or `ray <https://ray.readthedocs.io/en/latest/>`_) which however is quite easy to use 
and mostly compatible with Python multiprocessing or concurrent.futures. The concurrency architecture is the standard 
Single Writer Multiple Reader (SWMR), used at the HDF5 level: only one process can write data while multiple processes 
can read it. The engine runs seamlessly on a single machine or a cluster, using as many cores as possible.

In the past the engine had a database-centric architecture and was more class-oriented than numpy-oriented: some remnants 
of such dark past are still there, but they are slowly disappearing. Currently the database is only used for storing 
accessory data and it is a simple SQLite file. It is mainly used by the WebUI to display the logs.

Components of the OpenQuake engine
----------------------------------

The OpenQuake engine suite is composed of several components:

- a set of **support libraries** addressing different concerns like reading the inputs and writing the outputs, implementing basic geometric manipulations, managing distributed computing and generic programming utilities
- the **hazardlib** and **risklib** scientific libraries, providing the building blocks for hazard and risk calculations, notably the GMPEs for hazard and the vulnerability/fragility functions for risk
- the hazard and risk **calculators**, implementing the core logic of the engine
- the **datastore**, which is an HDF5 file working as a short term storage/cache for a calculation; it is possible to run a calculation starting from an existing datastore, to avoid recomputing everything every time; there is a separate datastore for each calculation
- the **database**, which is a SQLite file working as a long term storage for the calculation metadata; the database contains the start/stop times of the computations, the owner of a calculation, the calculation descriptions, the performances, the logs, etc; the bulk scientific data (essentially big arrays) are kept in the datastore
- the **DbServer**, which is a service mediating the interaction between the calculators and the database
- the **WebUI** is a web application that allows to run and monitor computations via a browser; multiple calculations can be run in parallel
- the **oq command-line** tool; it allows to run computations and provides an interface to the underlying database and datastores so that it is possible to list and export the results
- the engine can run on a cluster of machines: in that case a minimal amount of configuration is needed, whereas in single machine installations the engine works out of the box
- since v3.8 the engine does not depend anymore from celery and rabbitmq, but can still use such tools until they will be deprecated

This is the full stack of internal libraries used by the engine. Each of these is a Python package containing several 
modules or event subpackages. The stack is a dependency tower where the higher levels depend on the lower levels but not 
vice versa:

- **level 9**: commands (subcommands of oq)
- **level 8**: server (database and Web UI)
- **level 7**: engine (command-line tool, export, logs)
- **level 6**: calculators (hazard and risk calculators)
- **level 5**: commonlib (configuration, logic trees, I/O)
- **level 4**: risklib (risk validation, risk models, risk inputs)
- **level 3**: hmtk (catalogues, plotting, …)
- **level 2**: hazardlib (validation, read/write XML, source and site objects, geospatial utilities, GSIM library)
- **level 1**: baselib (programming utilities, parallelization, monitoring, hdf5…)

*baselib* and *hazardlib* are very stable and can be used outside of the engine; the other libraries are directly related 
to the engine and are likely to be affected by backward-incompatible changes in the future, as the code base evolves.

The GMPE library in *hazardlib* and the calculators are designed to be extensible, so that it is easy to add a new GMPE 
class or a new calculator. We routinely add several new GMPEs per release; adding new calculators is less common and it 
requires more expertise, but it is possible and it has been done several times in the past. In particular it is often 
easier to add a specific calculator optimized for a given use case rather than complicating the current calculators.

The results of a computation are automatically saved in the datastore and can be exported in a portable format, such as 
CSV (or XML, for legacy reasons). You can assume that the datastore of version X of the engine will not work with version 
X + 1. On the contrary, the exported files will likely be same across different versions. It is important to export all 
of the outputs you are interested in before doing an upgrade, otherwise you would be forced to downgrade in order to be 
able to export the previous results.

The WebUI provides a REST API that can be used in third party applications: for instance a QGIS plugin could download the 
maps generated by the engine via the WebUI and display them. There is lot of functionality in the API which is documented 
here: `gem/oq-engine <https://github.com/gem/oq-engine/blob/master/doc/web-api.md>`. It is possible to build your own user 
interface for the engine on top of it, since the API is stable and kept backward compatible.

Design principles
-----------------

The main design principle has been *simplicity*: everything has to be as simple as possible (but not simplest). The goal 
has been to keep the engine simple enough that a single person can understand it, debug it, and extend it without 
tremendous effort. All the rest comes from simplicity: transparency, ability to inspect and debug, modularity, 
adaptability of the code, etc. Even efficiency: in the last three years most of the performance improvements came from 
free, just from removing complications. When a thing is simple it is easy to make it fast. The battle for simplicity is 
never ending, so there are still several things in the engine that are more complex than they should: we are working on 
that.

After simplicity the second design goal has been *performance*: the engine is a number crunching application after all, 
and we need to run massively parallel calculations taking days or weeks of runtime. Efficiency in terms of computation 
time and memory requirements is of paramount importance, since it makes the difference between being able to run a 
computation and being unable to do it. Being too slow to be usable should be considered as a bug.

The third requirement is *reproducibility*, which is the same as testability: it is essential to have a suite of tests 
checking that the calculators are providing the expected outputs against a set of predefined inputs. Currently we have 
thousands of tests which are run multiple times per day in our Continuous Integration environments (GitHub Actions, 
GitLab Pipelines), split into unit tests, end-to-end tests and long running tests.

How the parallelization works in the engine
-------------------------------------------

The engine builds on top of existing parallelization libraries. Specifically, on a single machine it is based on 
multiprocessing, which is part of the Python standard library, while on a cluster it is based on zeromq, which is a 
well-known and maintained library.

While the parallelization used by the engine may look trivial in theory (it only addresses embarrassingly parallel 
problems, not true concurrency) in practice it is far from being so. For instance a crucial feature that the GEM staff 
requires is the ability to kill (revoke) a running calculation without affecting other calculations that may be running 
concurrently.

Because of this requirement, we abandoned *concurrent.futures*, which is also in the standard library, but is lacking 
the ability to kill the pool of processes, which is instead available in multiprocessing with the *Pool.shutdown* method. 
For the same reason, we discarded *dask*.

Using a real cluster scheduling mechanism (like SLURM) would be of course better, but we do not want to impose on our 
users a specific cluster architecture. Zeromq has the advantage of being simple to install and manage. Still, the 
architecture of the engine parallelization library is such that it is very simple to replace zeromq with other 
parallelization mechanisms: people interested in doing so should just contact us.

Another tricky aspect of parallelizing large scientific calculations is that the amount of data returned can exceed the 
4 GB limit of Python pickles: in this case one gets ugly runtime errors. The solution we found is to make it possible 
to yield partial results from a task: in this way instead of returning say 40 GB from one task, one can yield 40 times 
partial results of 1 GB each, thus bypassing the 4 GB limit. It is up to the implementor to code the task carefully. In 
order to do so, it is essential to have in place some monitoring mechanism measuring how much data is returned back 
from a task, as well as other essential information like how much memory is allocated and how long it takes to run a 
task.

To this aim the OpenQuake engine offers a ``Monitor`` class (located in ``openquake.baselib.performance``) which is 
perfectly well integrated with the parallelization framework, so much that every task gets a ``Monitor`` object, a 
context manager that can be used to measure time and memory of specific parts of a task. Moreover, the monitor 
automatically measures time and memory for the whole task, as well as the size of the returned output (or outputs). 
Such information is stored in an HDF5 file that you must pass to the monitor when instantiating it. The engine 
automatically does that for you by passing the pathname of the datastore.

In OpenQuake engine a task is just a Python function (or generator) with positional arguments, where the last argument is a 
``Monitor`` instance. For instance the rupture generator task in an event based calculation is coded more or less like 
this::

	def sample_ruptures(sources, num_samples, monitor):  # simplified code
	    ebruptures = []
	    for src in sources:
	        for ebr in src.sample_ruptures(num_samples):
	            eb_ruptures.append(ebr)
	        if len(eb_ruptures) > MAX_RUPTURES:
	            # yield partial result to avoid running out of memory
	            yield eb_ruptures
	            eb_ruptures.clear()
	    if ebruptures:
	        yield eb_ruptures

If you know that there is no risk of running out of memory and/or passing the pickle limit you can just use a regular 
function and return a single result instead of yielding partial results. This is the case when computing the hazard 
curves, because the algorithm is considering one rupture at the time and it is not accumulating ruptures in memory, 
differently from what happens when sampling the ruptures in event based.

From the point of view of the coder, in the engine there is no difference between a task running on a cluster using 
zeromq and a task running locally using ``multiprocessing.Pool:`` they are coded the same, but depending on a 
configuration parameter in openquake.cfg (``distribute=zmq`` or ``distribute=processpool``) the engine will treat them 
differently. You can also set an environment variable ``OQ_DISTRIBUTE``, which takes the precedence over openquake.cfg, 
to specify which kind of distribution you want to use (``zmq`` or ``processpool``): this is mostly used when debugging, 
when you typically insert a breakpoint in the task and then run the calculation with::

	$ OQ_DISTRIBUTE=no oq run job.ini

``no`` is a perfectly valid distribution mechanism in which there is actually no distribution and all the tasks run 
sequentially in the same core. Having this functionality is invaluable for debugging.

Another tricky bit of real life parallelism in Python is that forking does not play well with the HDF5 library: so in 
the engine we are using multiprocessing in the ``spawn`` mode, not in ``fork`` mode: fortunately this feature has become 
available to us in Python 3 and it made our life a lot happier. Before it was extremely easy to incur unspecified 
behavior, meaning that reading an HDF5 file from a forked process could

1. work perfectly well
2. read bogus numbers
3. cause a segmentation fault

and all of the three things could happen unpredictably at any moment, depending on the machine where the calculation was 
running, the load on the machine, and any kind of environmental circumstances.

Also, while with the newest HDF5 libraries it is possible to use a Single Writer Multiple Reader architecture (SWMR), 
and we are actually using it - even if it is sometimes tricky to use it correctly - the performance is not always good. 
So, when it matters, we are using a two files approach which is simple and very effective: we read from one file (with 
multiple readers) and we write on the other file (with a single writer). This approach bypasses all the limitations of 
the SWMR mode in HDF5 and did not require a large refactoring of our existing code.

Another tricky point in cluster situations is that we need to transfer gigabytes of data, i.e. the large arrays coming 
from scientific calculations, rather than lots of small messages. Hence, we are returning data from the tasks via 
zeromq instead of using celery/rabbitmq as we did in the remote past. This is hidden from the user, but internally the 
engine keeps track of all tasks that were submitted and waits until they send the message that they finished. If one 
task runs out of memory badly and never sends the message that it finished, the engine may hang, waiting for the 
results of a task that does not exist anymore. You have to be careful. What we did in our cluster is to set some memory 
limit on the openquake user with the cgroups technology, so that an out of memory task normally fails in a clean way 
with a Python MemoryError, sends the message that it finished and nothing particularly bad happens. Still, in situations 
of very heavy load the OOM killer may enter in action aggressively and the main calculation may hang: in such cases you 
need a good sysadmin having put in place some monitor mechanism, so that you can see if the OOM killer entered in action 
and then you can kill the main process of the calculation by hand. There is not much more that can be done for really 
huge calculations that stress the hardware as much as possible. You must be prepared for failures.

*************************************
How to use openquake.baselib.parallel
*************************************

Suppose you want to code a character-counting algorithm, which is a textbook exercise in parallel computing and suppose 
that you want to store information about the performance of the algorithm. Then you should use the OpenQuake Monitor 
class, as well as the utility ``openquake.baselib.commonlib.hdf5new`` that builds an empty datastore for you. Having done 
that, the ``openquake.baselib.parallel.Starmap`` class can take care of the parallelization for you as in the following 
example::

	import os
	import sys
	import pathlib
	import collections
	from openquake.baselib.performance import Monitor
	from openquake.baselib.parallel import Starmap
	from openquake.commonlib.datastore import hdf5new
	
		
	def count(text):
	    c = collections.Counter()
	    for word in text.split():
	        c += collections.Counter(word)
	    return c
	
	
	def main(dirname):
	    dname = pathlib.Path(dirname)
	    with hdf5new() as hdf5:  # create a new datastore
	        monitor = Monitor('count', hdf5)  # create a new monitor
	        iterargs = ((open(dname/fname, encoding='utf-8').read(),)
	                    for fname in os.listdir(dname)
	                    if fname.endswith('.rst'))  # read the docs
	        c = collections.Counter()  # intially empty counter
	        for counter in Starmap(count, iterargs, monitor):
	            c += counter
	        print(c)  # total counts
	        print('Performance info stored in', hdf5)
	
	
	if __name__ == '__main__':
	    main(sys.argv[1])  # pass the directory where the .rst files are

The name ``Starmap`` was chosen because it looks very similar to how ``multiprocessing.Pool.starmap`` works, the only 
apparent difference being in the additional monitor argument::

	pool.starmap(func, iterargs) ->  Starmap(func, iterargs, monitor)

In reality the ``Starmap`` has a few other differences:

1. it does not use the multiprocessing mechanism to return back the results; it uses zmq instead
2. thanks to that, it can be extended to generator functions and can yield partial results, thus overcoming the limitations of multiprocessing
3. the ``Starmap`` has a ``.submit`` method and it is actually more similar to ``concurrent.futures`` than to multiprocessing.

Here is how you would write the same example by using ``.submit``::

	def main(dirname):
	    dname = pathlib.Path(dirname)
	    with hdf5new() as hdf5:
	        smap = Starmap(count, monitor=Monitor('count', hdf5))
	        for fname in os.listdir(dname):
	            if fname.endswith('.rst'):
	                smap.submit(open(dname/fname, encoding='utf-8').read())
	        c = collections.Counter()
	        for counter in smap:
	            c += counter

The difference with ``concurrent.futures`` is that the ``Starmap`` takes care for of all submitted tasks, so you do not 
need to use something like ``concurrent.futures.completed``, you can just loop on the ``Starmap`` object to get the 
results from the various tasks.

The ``.submit`` approach is more general: for instance you could define more than one ``Starmap`` object at the same 
time and submit some tasks with a starmap and some others with another starmap: this may help parallelizing complex 
situations where it is expensive to use a single starmap. However, there is limit on the number of starmaps that can be 
alive at the same moment.

Moreover the ``Starmap`` has a ``.shutdown`` method that allows to shutdown the underlying pool.

The idea is to submit the text of each file - here I am considering .rst files, like the ones composing this manual - 
and then loop over the results of the ``Starmap``. This is very similar to how ``concurrent.futures`` works.