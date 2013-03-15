The risklite library
=========================================


The `risklite` library provides support for running risk computations
by using the calculators in risklib. It has utilities to read ground
motion fields, exposures, vulnerability and fragility models from csv
files; it has also utilities to write loss maps and damage
distributions in csv format.  Moreover it provides several pre-built
calculators. The list of available calculators can be obtained
as follows:

>>> from openquake.risklite.calculators import registy
>>> sorted(registry)
['scenario', 'scenario_damage', ...]

Running a risk computation for a predefined calculator
involves two simple steps:

- put in a directory all the needed input files, plus an .ini
  file specifying the files and the calculator to use
- launch the script

    $ run_risk <input_directory> <config.ini>

For instance for a scenario computation the needed files are:

- the ground motion fields, gmf.csv, in the format
  ``lon lat gmv1 ... gmvN`` where ``N`` is the number of realizations
  of the ground motion field; the file must be tab separated
- the exposure file, exposure.csv, in the format
  ``lon lat asset_ref number_of_units taxonomy```
- the vulnerability functions, vulnerability.csv, in the format
  ``taxonomy IMT [iml...] [loss_ratio...] [cov...] distribution``

A valid configuration file could be the following::

  $ cat job.ini
  [general]

  description = Scenario Risk Nepal
  calculation_mode = scenario
  
  vulnerability_file = vulnerability_model.csv
  exposure_file = exposure_model.csv.gz
  gmf_file = gmf.csv.gz
  
  export_dir = /tmp
  
Notice the parameter ``export_dir``, which is used as the directory where
to write the results.

`risklite` can be used as a library too. There is a helper function
`openquake.risklite.parallel.run_calc(path, runner, config)` which is able
to run an end-to-end computation. To use it, you must first instantiate
a `Runner` object, which in turn requires an executor object.
The executor comes from the Python library
`concurrent.futures`, which is part of the standard library
starting from Python 3.3 and which can be installed even in
older versions of Python. At the moment the recommended
way to perform risk computations is to instantiate a
`ProcessPoolExecutor` and to pass it to the runner:

>>> from concurrent.futures import ProcessPoolExecutor
>>> from openquake.risklite.parallel import run_calc, Runner
>>> runner = Runner(ProcessPoolExecutor())

Then it is possible to run the computation as follows:

>>> ctxt = run_calc(path, runner, 'job.ini')

``ctxt`` is a dictionary containing the context of the computation;
in particular it has keys for all the parameters in the configuration file.
It also contains the parsed input files: in particular the exposure
assets, ordered by taxonomy.

How the parallelization works
----------------------------------------------

The ``Runner`` class in ``risklite.parallel`` provides a simple way
to parallelize computations, which is suitable for risk calculations.
It is however possible to implement different strategies. The only
requirements on runner objects are the following:

- the runner object must have a ``.run`` method which must be called
  with a callable, a sequence and possibly other optional arguments;
- the callable must accept a sequence as first argument.

``runner.run(func, sequence)`` takes the sequence and splits it in
chunks of a given chunksize, then it applies ``func`` to each chunk
and collects the results. In risk computations the sequence is
a list of hazard values and ``func`` is a risklib calculator;
the output is a list of numpy arrays.
The regular ``Runner`` class uses the executor to submit the computation
to a pool of workers (processes if using
:class:concurrent.futures.ProcessPoolExecutor, threads if using
:class:concurrent.futures.ThreadPoolExecutor); it is responsibility
of the client code to shutdown the pool at the end of the
computation. Since it is pretty difficult to debug error in
parallel code, ``risklite.parallel`` provides a ``BaseRunner`` class too:
it has the same interface of the ``Runner`` class, but it actually
runs the operations sequentially in the same process, so that the
Python debugger works, the traceback is not lost and the programmer
experience is generally nicer, apart from the fact that only a single
core is used, i.e. the computation is expected to be slower.


Defining new calculators
----------------------------------

It is pretty easy to define a new risklite calculator. Define a
function with signature ``mycalculator(inputdic, runner)`` and
register it with a ``calculation_mode`` string::

 registry[<calculation_mode>] = mycalculator

There is also a decorator to perform the registration automatically:

.. code-block: python

 @registry.add(<calculation_mode>)
 def mycalculator(ctxt, runner):
     pass

Then the new calculator can be used immediately. The calculator function
should not return anything, but it can populate the ``ctxt`` dictionary.
Internally the calculator will use the ``runner`` to run computations
(usually involving the risklib core calculators) in parallel.
