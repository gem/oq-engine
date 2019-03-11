How the parallelization works in the engine
===========================================

The engine builds on top of existing parallelization libraries.
Specifically, on a single machine it is based on multiprocessing,
which is part of the Python standard library, while on a cluster
it is based on the combination celery/rabbitmq, which are well known
and maintained tools.

While the parallelization used by the engine may look trivial in theory
(it only addresses embarrassingly parallel problems, not true concurrency)
in practice it is far from being so. For instance a crucial feature that
the GEM staff requires is the ability to kill (revoke) a running calculation
without affecting other calculations that may be running concurrently,
because

Because of this requirement we abandoned `concurrent.futures`, which is also
in the standard library, but is lacking the ability to kill the pool of
processes, which is instead available in multiprocessing with the
`Pool.shutdown` method. For the same reason, we discarded `dask`, which
is a lot more powerful than `celery` but lacks the revoke functionality.

Using a real cluster scheduling mechanism (like SLURM) would be of course
better, but we do not want to impose to our users a specific cluster
architecture. celery/rabbitmq have the advantage of being simple to install
and manage. Still, the architecture of the engine parallelization library
is such that it is very simple to replace celery/rabbitmq with other
parallelization mechanisms: people interested in doing so should just
contact us.

Another tricky aspects of parallelizing large scientific calculations is
that the amount of data returned can exceed the 4 GB limit of Python pickles:
in this case one gets ugly runtime errors. The solution we found is to make
it possible to yield partial results from a task: in this way instead of
returning say 40 GB from one task, one can yield 40 times partial results
of 1 GB each, thus bypassing the 4 GB limit. It is up to the implementor
to code the task carefully. In order to do so, it is essential to have
in place some monitoring mechanism measuring how much data is returned
back from a task, as well as other essential informations like how much
memory is allocated and how long it takes to run a task.

To this aim the OpenQuake engine offers a ``Monitor`` class
(located in ``openquake.baselib.performance``) which is perfectly well
integrated with the parallelization framework, so much that every
task gets a ``Monitor`` object, a context manager that can be used
to measure time and memory of specific parts of a task. Moreover,
the monitor automatically measure time and memory for the whole task,
as well as the size of the returned output (or outputs). Such information
is stored in an HDF5 file that you must pass to the monitor when instantiating
it. The engine automatically does that for you by passing the pathname of the
datastore.

In OpenQuake a task is just a Python function (or generator)
with positional arguments, where the last argument is a ``Monitor`` instance.
For instance the rupture generator task in an event based calculation
is coded more or less like this:

.. code-block::

   def sample_ruptures(sources, num_samples, monitor):  # simplified code
       ebruptures = []
       for src in sources:
           for rup, n_occ in src.sample_ruptures(num_samples):
               ebr = EBRupture(rup, src.id, grp_id, n_occ)
               eb_ruptures.append(ebr)
           if len(eb_ruptures) > MAX_RUPTURES:
               # yield partial result to avoid running out of memory
               yield eb_ruptures
               eb_ruptures.clear()
       if ebruptures:
           yield eb_ruptures

If you know that there is no risk of running out of memory and/or passing the
pickle limit you can just use a regular function and return a single result
instead of yielding partial results. This is the case when computing the
hazard curves, because the algorithm is considering one rupture at the time
and it is not accumulating ruptures in memory, differently from what happens
when sampling the ruptures in event based.

If you have ever coded in celery, you will see that the OpenQuake engine
concept of task is different: there is no ``@task`` decorator and while at the
end engine tasks will become celery tasks this is hidden to the developer.
The reason is that we needed a celery-independent abstraction layer to make
it possible to use different kinds of parallelization frameworks/

From the point of view of the coder, in the engine there is no difference
between a task running on a cluster using celery and a task running locally
using ``multiprocessing.Pool``: they are coded the same, but depending
on a configuration parameter in openquake.cfg (``distribute=celery``
or ``distribute=processpool``) the engine will treat them differently.
You can also set an environment variable ``OQ_DISTRIBUTE``, which takes
the precedence over openquake.cfg, to specify which kind of distribution
you want to use (``celery`` or ``processpool``): this is mostly used
when debugging, when you typically insert a breakpoint in the task
and then run the calculation with

.. code-block: bash

   $ OQ_DISTRIBUTE=no oq run job.ini

``no`` is a perfectly valid distribution mechanism in which there is actually
no distribution and all the tasks run sequentially in the same core. Having
this functionality is invaluable for debugging.

Another tricky bit of real life parallelism in Python is that forking
does not play well with the HDF5 library: so in the engine we are
using multiprocessing in the ``spawn`` mode, not in ``fork`` mode:
fortunaly this feature has become available to us in Python 3 and it
made our life a lot happier.  Before it was extremely easy to incurr
in unspecified behavior, meaning that reading an HDF5 file from a
forked process could

1. work perfectly well
2. read bogus numbers
3. cause a segmentation fault

and all of the three things could happen impredictably at any moment, depending
on the machine where the calculation was running, the load on the machine, and
any kind of environmental circumstances.

Also, while in theory with the newest HDF5 libraries it should be
possible to use a SWMR architecture (Single Writer Multiple Reader) we
were not able to get this working in the engine. Instead, we are using
a two files approach which is simple and works very well: we read from
one file (with multiple readers) and we write on the other file
(with a single writer), insteading or reading/writing
on the same file. This bypasses all the limitations of the SWMR mode
in HDF5 and did not require a large refactoring of our existing code.

Another tricky point in cluster situations is that rabbitmq is not good
at transferring gigabytes of data: it was meant to manage lots of small
messages, but here we are perverting it to manage huge messages, i.e.
the large arrays coming from a scientific calculations.

Hence, since recent versions of the engine we are no more returning
data from the tasks via celery/rabbitmq: instead, we use zeromq.  This
is hidden from the user, but internally the engine keeps track of all
tasks that were submitted and waits until they send the message that
they finished. If one tasks runs out of memory badly and never sends
the message that it finished, the engine may hang, waiting for the
results of a task that does not exist anymore.  You have to be
careful. What we did in our cluster is to set some memory limit on the
celery user with the cgroups technology, so that an out of memory task
normally fails in a clean way with a Python MemoryError, sends the
message that it finished and nothing particularly bad happens.  Still,
in situations of very heavy load the OOM killer may enter in action
aggressively and the main calculation may hang: in such cases you need
a good sysadmin having put in place some monitor mechanism, so that
you can see if the OOM killer entered in action and then you can kill
the main process of the calculation by hand. There is not much more
that can be done for really huge calculations that stress the hardware
as much as possible. You must be prepared for failures.


How to use openquake.baselib.parallel
-------------------------------------

Suppose you want to code a character-counting algorithm, which is a textbook
exercise in parallel computing and suppose that you want to store information
about the performance of the algorithm. Then you should use the OpenQuake
``Monitor`` class, as well as the utility
``openquake.baselib.datastore.hdf5new`` that build an empty datastore
for you. Having done that, the ``openquake.baselib.parallel.Starmap``
class can take care of the parallelization for you as in the following
example:

.. include:: char_count_par.py
   :code: python

The name ``Starmap`` was chosen it looks very similar to
``multiprocessing.Pool.starmap`` works, the only apparent difference
being in the additional monitor argument::

    pool.starmap(func, iterargs) ->  Starmap(func, iterargs, monitor)

In reality the ``Starmap`` has a few other differences:

1. it does not use the multiprocessing mechanism to returns back the results,
   it uses zmq instead;
2. thanks to that, it can be extended to generator functions and can yield
   partial results, thus overcoming the limitations of multiprocessing
3. the ``Starmap`` has a ``.submit`` method and it is actually more similar to
   ``concurrent.futures`` than to multiprocessing.

Here is how you would write the same example by using ``.submit``:

.. code-block::

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

The difference with ``concurrent.futures`` is that
the ``Starmap`` takes care for of all submitted tasks, so you do not
need to use something like ``concurrent.futures.completed``, you can just
loop on the ``Starmap`` object to get the results from the various tasks.

The ``.submit`` approach is more general: for instance you could define
more than one ``Starmap`` object at the same time and submit some tasks
with a starmap and some others with another starmap: this may help
parallelizing complex situations where it is expensive to use a single
starmap. However, there is limit on the number of starmaps that can be
alive at the same moment.

Moreover the ``Starmap`` has a ``.shutdown`` methods that allows to
shutdown the underlying pool.

The idea is to submit the text of each file - here I am considering .rst files,
like the ones composing this manual - and then loop over the results of the
``Starmap``. This is very similar to how ``concurrent.futures`` works,
