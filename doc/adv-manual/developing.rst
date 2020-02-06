Developing with the engine
==========================

Some advanced users are interested in developing with the engine,
usually to contribute new GMPEs and sometimes to submit a bug fix.
There are also users interested in implementing their own customizations
of the engine. This part of the manual is for them.

Prerequisites
-------------------

It is assumed here that you are a competent scientific Python
programmer, i.e. that you have a good familiarity with the Python
ecosystem (including pip and virtualenv) and its scientific stack
(numpy, scipy, h5py, ...). It should be noticed that since engine v2.0
there is no need to know anything about databases and web development
(unless you want to develop on the WebUI part) so the barrier for
contribution to the engine is much lower than it used to be. However,
contributing is still nontrivial, and it absolutely necessary
to know git and the tools of Open Source development in
general, in particular about testing. If this is not the
case, you should do some study on your own and come back later. There
is a huge amount of resources in the net about these topics. This
manual will focus solely on the OpenQuake engine and it assume that
you already know how to use it, i.e. you have read the User Manual
first.

Before starting, it may be useful to have an idea of the architecture
of the engine and its internal components, like the DbServer and the
WebUI. For that you should read the :ref:`architecture` document.

There are also external tools which are able to interact with the engine,
like the QGIS plugin to run calculations and visualize the outputs and the
IPT tool to prepare the required input files (except the hazard models).
Unless you are developing for such tools you can safely ignore them.

The first thing to do
---------------------

The first thing to do if you want to develop with the engine is to remove
any non-development installation of the engine that you may have. While it
is perfectly possible to install on the same machine both a development and
a production instance of the engine (it is enough to configure the ports
of the DbServer and WebUI) it is easier to work with a single instance.
In that way you will have a single code base and no risks of editing the
wrong code. A development installation the engine works as any other
development installation in Python: you should clone the engine repository,
create and activate a virtualenv and then perform a `pip install -e .`
from the engine main directory, as normal. You can find the details here:

https://github.com/gem/oq-engine/blob/master/doc/installing/development.md

It is also possible to develop on Windows (
https://github.com/gem/oq-engine/blob/master/doc/installing/development.md)
but very few people in GEM are doing that, so you are on your own, should you
encounter difficulties. We recommend Linux, but Mac also works.

Since you are going to develop with the engine, you should also install
the development dependencies that by default are not installed. They
are listed in the setup.py file, and currently (January 2020) they are
pytest, flake8, pdbpp, silx and ipython. They are not required but very
handy and recommended. It is the stack we use daily for development.

Understanding the engine
-------------------------

Once you have the engine installed you can run calculations. We recommend
starting from the demos directory which contains example of hazard and
risk calculations. For instance you could run the area source demo with the
following command::

 $ oq run demos/hazard/AreaSourceClassicalPSHA/job.ini 

You should notice that we used here the command `oq run` while the engine
manual recommend the usage of `oq engine --run`. There is no contradiction.
The command `oq engine --run` is meant for production usage, it will work
with the WebUI and store the logs of the calculation in the engine database.
But here we are doing development, so the recommended command is `oq run`
which will not interact with the database, will be easier to debug and
accept the essential flag ``--pdb``, which will start the python debugger
should the calculation fail. Since during development is normal to have
errors and problems in the calculation, so this ability is invaluable.

Then, if you want to understand what happened during the calculation
you should generate the associated .rst report, which can be seen with
the command

``$ oq show fullreport``

There you will find a lot of interesting information that it is worth studying
and we will discuss in detail in the rest of this manual. The most important
section of the report is probably the last one, titled "Slowest operations".
For that one can understand the bottlenecks of the calculation and, with
experience, he can understand which part of the engine he needs to optimize.
Also, it is very useful to play with the parameters of the calculation
(like the maximum distance, the area discretization, the magnitude binning,
etc etc) and see how the performance change. There is also a command to
plot hazard curves and a command to compare hazard curves between different
calculations: it is common to be able to get big speedups simply by changing
the input parameters in the `job.ini` of the model, without changing much the
results.

There a lot of `oq` commands: if you are doing development you should study
all of them. They are documented here_.

.. _here: oq-commands.md
