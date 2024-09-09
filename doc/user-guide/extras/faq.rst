.. _faq:

Frequently Asked Questions (FAQ)
================================

FAQ for IT issues
-----------------

******************************************************************
Help! What is the recommended hardware to run engine calculations?
******************************************************************

It depends on your use case and your level of expertise. Most of our users are scientists with little IT experience
and/or little support from their IT departments. For them we recommend to buy a very powerful server and not a cluster,
which is complex to manage. A server with 256 GB of RAM and 64 real cores is currently powerful enough to run all of the
calculations in the GEM global hazard and risk mosaic. If you have larger calculations and IT expertise, for a cluster
setup see the pages :ref:`cluster <cluster>` 
and :ref:`FAQ related to cluster deployments <faq-cluster>`.

***********************************************************
Help! Should I disable hyperthreading on my laptop/desktop?
***********************************************************

While in old versions of the engine we recommended to disable hyperthreading
- which was often difficult for our users and sometimes impossible -
since version 3.21 the engine on Windows, by default, will only use half of
your threads, which is a simple and efficient way to save
memory. Consider for instance a laptop with an i7
processor with 8 cores, 16 threads and 16 GB of RAM. It seems a lot:
in reality it is not. The operating system will consume some memory,
the browser will consume a lot of memory, you may have other
applications open and you may end up with less than 8 GB of available
memory. Running even small computations may easily consume 0.5 GB per
thread, i.e. 8 GB, so you will run out of memory. However, since
engine v3.21, the engine by default will only use 8 threads, thus each one
will have 1 GB of RAM available. This is still not much (we recommend
2 GB) but enough to run most calculations. If you want more control, by setting
the parameter ``num_cores`` in the file `openquake.cfg` (as explained
below) it is possible to specify precisely the number of threads to
use and this will work on every operating system.

*******************************************************
Help! My windows server with 32/64 or more cores hangs!
*******************************************************

Some users reported this issue. It is due to a limitation of Python
multiprocessing module on Windows. In all cases we have seen, the
problem was solved by disabling hyperthreading. Otherwise you can
reduce the number of used cores by setting the parameter ``num_cores``
in the file `openquake.cfg` as explained below.

************************************************************
Help! I want to limit the number of cores used by the engine
************************************************************

This is another way to save memory. If you are on a single machine,
the way to do it is to edit the file `openquake.cfg` and add the lines
(if for instance you want to use 8 cores)::

	[distribution]
	num_cores = 8

If you are on a cluster you must edit the section [zworkers] and the
parameter ``host_cores``, replacing the ``-1`` with the number of
cores to be used on each machine.

*********************************
Help! I am running out of memory!
*********************************

If you are on a laptop, the first thing to do is close all memory consuming applications. Remember that running the
engine from the command-line is the most memory-efficient way to run calculations (browsers can use significant memory
from your laptop). You can also limit the number of parallel threads as explained before (i.e. disable hyperthreading,
reduce num_cores) or disable parallelism altogether. If you still run out of memory, then you must reduce your
calculation or upgrade your system.

*************************************
Help! I am running out of disk space!
*************************************

By default the engine stores the calculations in the directory $HOME/oqdata.
If there is not much space on that partition you may run out of disk space.
The solution is to change the location where the calculations are stored,
pointing to an external disk or in general to a partition with a lot of
space. You can do it temporarily by setting the environment variable
OQ_DATADIR or permanently by changing the `openquake.cfg` file and
adding a couple of lines like::

  [directory]
  shared_dir = /mnt/largedisk

Then the data will be stored in `/mnt/largedisk/<username>/oqdata`.

*****************************************************************************************************************
Help! Is it possible to configure multiple installations of the engine to run independently on the same computer?
*****************************************************************************************************************

Yes, it is possible, as long as their virtual environments are stored in different directories.

When you install the engine using the ``install.py`` script, you may specify the ``--venv`` parameter to choose in which
directory the engine virtual environment must be stored. On an existing installation of the engine, you can run the
command::

	$ oq info venv

to retrieve the path of its virtual environment.

Another parameter accepted by the ``install.py`` script is
``--dbport``, that specifies the port number used by the engine
dbserver. This is only relevant for server installations.  By default,
the port is set to 1907. The port can be customized through the
attribute ``port`` of section ``[dbserver]`` in the configuration file
``openquake.cfg``, placed inside the virtual environment directory,
e.g.::

	[dbserver]
        port = 1908

########################################################################
Can two installations of the engine share the same ``oqdata`` directory?
########################################################################

The ``oqdata`` directory, that stores calculation data, can safely be shared between two different instances of the
engine working on a same computer. Each HDF5 dataset is independent from all others in the datastore and it has a unique
identifier. It is possible to determine the version of the engine that produced each HDF5 file (``calc_<calc_id>.hdf5``)
using the command::

	$ oq show_attrs / <calc_id>

where ``/`` indicates the root attributes (date, engine_version, etc.) and ``<calc_id>`` (an integer number) is the
calculation identifier. In case the calculation id is not specified, the attributes are retrieved for the latest
calculation.

-------

******************************
Different installation methods
******************************

The OpenQuake engine has several installation methods. To choose the one that best fits your needs take a look at the
:ref:`installation overview <installing-the-openquake-engine>`.

###########################
Supported operating systems
###########################

Binary packages are `provided for Windows <https://downloads.openquake.org/pkgs/windows/oq-engine>`__.  For all other
systems use the :ref:`universal installer <universal>`. We also provide :ref:`Docker containers <docker>`.

Binary packages are provided for the following 64bit operating systems::

- Windows 10
- macOS 11.6+
- Linux Ubuntu 18.04+ and RedHat/CentOS 7/RockyLinux 8 via deb and rpm
- Any other generic Linux distribution via the universal installer
- Docker hosts

A 64bit operating system **is required**. Please refer to each OS specific page for details about requirements.

.. _unsupported-operating-systems:

#############################
Unsupported operating systems
#############################

- Windows 8 may or may not work and we will not provide support for it Binary packages *may* work on Ubuntu derivatives and Debian if the dependencies are satisfied; these configurations are known to work:
- Ubuntu 18.04 (Bionic) packages work on **Debian 10.0** (Buster)
- Ubuntu 20.04 (Focal) packages work on **Debian 11.0** (Bullseye)

These configurations however are not tested and we cannot guarantee on the quality of the results. Use at your own risk.

#############
32bit support
#############

The OpenQuake engine **requires a 64bit operating system**. Starting with version v2.3 of the Engine binary installers
and packages aren't provided for 32bit operating systems anymore.

.. _mpi-support:

###########
MPI support
###########

MPI is not supported by the OpenQuake engine. Task distribution across network interconnected nodes is done via *zmq*.
The worker nodes must have read access to a shared file system writeable from the master node. Data transfer is made on
TCP/IP connection.

MPI support may be added in the future if sponsored by someone. If you would like to help support development of
OpenQuake engine, please contact us at partnership@globalquakemodel.org.

-------

########################
Python 2.7 compatibility
########################

Support for Python 2.7 has been dropped. The last version of the Engine compatible with Python 2.7 is
OpenQuake engine version 2.9 (Jeffreys).

####################################
Python scripts that import openquake
####################################

If a third party python script (or a Jupyter notebook) needs to import openquake as a library
(as an example: ``from openquake.commonlib import readinput``) you must use a virtual environment and install a local
copy of the Engine::

	$ python3 -m venv </path/to/myvenv>
	$ . /path/to/myvenv/bin/activate
	$ pip3 install openquake.engine


##########################################################
'The openquake master lost its controlling terminal' error
##########################################################

When the OpenQuake engine is driven via the ``oq`` command over an SSH connection an associated terminal must exist
throughout the ``oq`` calculation lifecycle. The ``openquake.engine.engine.MasterKilled: The openquake master lost its
controlling terminal`` error usually means that the SSH connection has dropped or the controlling terminal has been
closed having a running computation attached to it.

To avoid this error please use ``nohup``, ``screen``, ``tmux`` or ``byobu`` when using ``oq`` via SSH. More information
is available on :ref:`Running the OpenQuake engine <unix>`.

.. _certificate-verification-on-macOS:

#################################
Certificate verification on macOS
#################################

On macOS you can get the following error::

	Traceback (most recent call last):
	  File "/Users/openquake/py36/bin/oq", line 11, in <module>
	    load_entry_point('openquake.engine', 'console_scripts', 'oq')()
	  File "/Users/openquake/openquake/oq-engine/openquake/commands/__main__.py", line 53, in oq
	    parser.callfunc()
	  File "/Users/openquake/openquake/oq-engine/openquake/baselib/sap.py", line 181, in callfunc
	    return self.func(**vars(namespace))
	  File "/Users/openquake/openquake/oq-engine/openquake/baselib/sap.py", line 251, in main
	    return func(**kw)
	  File "/Users/openquake/openquake/oq-engine/openquake/commands/engine.py", line 210, in engine
	    exports, hazard_calculation_id=hc_id)
	  File "/Users/openquake/openquake/oq-engine/openquake/commands/engine.py", line 70, in run_job
	    eng.run_calc(job_id, oqparam, exports, **kw)
	  File "/Users/openquake/openquake/oq-engine/openquake/engine/engine.py", line 341, in run_calc
	    close=False, **kw)
	  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 192, in run
	    self.pre_execute()
	  File "/Users/openquake/openquake/oq-engine/openquake/calculators/scenario_damage.py", line 85, in pre_execute
	    super().pre_execute()
	  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 465, in pre_execute
	    self.read_inputs()
	  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 398, in read_inputs
	    self._read_risk_data()
	  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 655, in _read_risk_data
	    haz_sitecol, assetcol)
	  File "/Users/openquake/openquake/oq-engine/openquake/calculators/base.py", line 821, in read_shakemap
	    oq.discard_assets)
	  File "/Users/openquake/openquake/oq-engine/openquake/hazardlib/shakemap.py", line 100, in get_sitecol_shakemap
	    array = download_array(array_or_id)
	  File "/Users/openquake/openquake/oq-engine/openquake/hazardlib/shakemap.py", line 74, in download_array
	    contents = json.loads(urlopen(url).read())[
	  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 223, in urlopen
	    return opener.open(url, data, timeout)
	  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 526, in open
	    response = self._open(req, data)
	  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 544, in _open
	    '_open', req)
	  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 504, in _call_chain
	    result = func(*args)
	  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 1361, in https_open
	    context=self._context, check_hostname=self._check_hostname)
	  File "/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/urllib/request.py", line 1320, in do_open
	    raise URLError(err)
	urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:852)>

Please have a look at ``/Applications/Python 3.8/ReadMe.rtf`` for possible solutions. If unsure run from a terminal the
following command::

	sudo /Applications/Python\ 3.8/install_certificates.command  # NB: use the appropriate Python version!

.. _faq-hazard:

FAQ about running hazard calculations
-------------------------------------

*************************************************************************
Can I estimate the runtime of a classical calculation without running it?
*************************************************************************

Since engine v3.15 you can. The trick is to run a reduced calculation first, by using the command::

	$ oq engine --run job.ini --sample-sources=0.01

This will reduce the number of ruptures by ~100 times so that the reduced calculation will complete in a reasonable
amount of time. Then in the log you will see the estimate runtime for the full calculation. For instance for the SHARE
model on a computer with an i7 processor you will see something like this::

	[2022-04-19 08:57:05 #4054 INFO] Estimated time 72.3 hours

The estimate is rather rough, so do not take it at the letter. The runtime can be reduced by orders of magnitude by
tuning parameters like the ``pointsource_distance`` and ``ps_grid_spacing``, discussed at length in the advanced manual.

****************************************************
Is the hazard reliable for all sites?
****************************************************

Users should be aware that there is a situation were hazard curves
are necessarily **unreliable**, i.e. very sensitive to small variations
in parameters such as the maximum distance and the minimum magnitude.

This happens when the low intensity part of the hazard curves is
well below 1. In an ideal world, for extremely small intensities
the probability of exceedence should tend to one; in the real
world, however, there is minimum magnitude and there is a
finite maximum distance, so ruptures are discarded from the
calculation. If enough ruptures are discarded, the probability of
exceedence will stay under 1, no matter how small the intensity is.
For poissonian curves the hazard curve is given by the formula

.. math::

  poe(iml) = 1 - e^{-(Σ r_i p_i(iml)) t}

where the sum is over the ruptures, :math:`r_i` is the occurrence rate,
:math:`p_i(iml)` is the probability of exceeding the intensity level
:math:`iml` and :math:`t` is the investigation time. For low
intensities the probabilities :math:`p_i(iml)` are at most 1
and the maximum poe can be approximated with

.. math::

  poe_{max} ~ (Σ r_i) t

which can be much smaller than 1 if the occurrence rate times the
investigation time is small and there are not many ruptures.  In this
situation a small change in the maximum distance or the minimum
magnitude can cause a large variation in the number of ruptures and
therefore a large change in :math:`poe_{max}`.  The worst case is when
:math:`poe_{max}` is below the reference `poe` used to compute the
hazard map. By definition, in this case the hazard map is zero and the
UHS contains at least a point of zero value. This situation is very
instable numerically: it is enough to slightly increase the
`maximum_distance` and a rupture that before was discarded can give a
small contribution, produce a hazard curve over the reference `poe`
and therefore a nonzero hazard map value.  The same will happen if you
change the geometry discretization step or the magnitude step. It is
even worse than that. Low hazard curves, in the region of small
intensities, tend to be flat, so even if the curve is slightly over
the reference poe, a small change to the curve will correspond to a
huge change in the intensity and therefore the hazard maps cannot be
reliably computed. This is unavoidable, low intensities are affected
by far away ruptures and low magnitude ruptures, and therefore very
sensitive to the way the engine (or the hazard modeler) cuts such
ruptures. Luckily, this has no practical effect on the risk, since the
assets on sites of low hazard are subjected to very low
damages. Still, the hazard scientist must be aware that hazard maps
and uniform hazard spectra cannot be trusted when the corresponding
hazard curves are below or close to the reference `poe` in the low
intensity region.

*************************************************
How should I interpret the "Realizations" output?
*************************************************

This is explained in the :ref:`logic trees section <logic-trees>`

****************************************************************
How do I export the hazard curves/maps/uhs for each realization?
****************************************************************

By default the engine only exports statistical results, i.e. the mean hazard curves/maps/uhs. If you want the individual
results you must set ``individual_rlzs=true`` in the job.ini files. Please take care: if you have thousands of realizations
(which is quite common) the data transfer and disk space requirements will be thousands of times larger than just
returning the mean results: the calculation might fail. This is why by default ``individual_rlzs`` is false.

*************************************************************************
Argh, I forgot to set ``individual_rlzs``! Must I repeat the calculation?
*************************************************************************

No, just set ``individual_rlzs=true`` in the job.ini and run::

	$ oq engine --run job.ini --hc=<ID> --exports csv

where ``<ID>`` must be replaced with the ID of the original calculation. The individual outputs will be regenerated by
reusing the result of the previous calculation: it will be a lot faster than repeating the calculation from scratch.

*************************************************************************
Argh, I set the wrong poes in the job.ini? Must I repeat the calculation?
*************************************************************************

No, set the right poes in the job.ini and as before run::

	$ oq engine --run job.ini --hc=<ID> --exports csv

where ``<ID>`` must be replaced with the ID of the original calculation. Hazard maps and UHS can be regenerated from an
existing calculation quite efficiently.

***********************************************************
I am getting an error "disaggregation matrix is too large"!
***********************************************************

This means that you have too many disaggregation bins. Please act on the binning parameters, i.e. on ``mag_bin_width``,
``distance_bin_width``, ``coordinate_bin_width``, ``num_epsilon_bins``. The most relevant parameter is ``coordinate_bin_width``
which is quadratic: for instance by changing from ``coordinate_bin_width=0.1`` to ``coordinate_bin_width=1.0`` the size of
your disaggregation matrix will be reduced by 100 times.

************************************************************************
What is the relation between sources, ruptures, events and realizations?
************************************************************************

A single rupture can produce multiple seismic events during the investigation time. How many depends on the number of
stochastic event sets, on the rupture occurrence rate and on the ``ses_seed`` parameters, as explained
:ref:`here <rupture-sampling-how-does-it-work>`. In the
engine a rupture is uniquely identified by a rupture ID, which is a 32 bit positive integer. Starting from engine v3.7,
seismic events are uniquely identified by an event ID, which is a 32 bit positive integer. The relation between event ID
and rupture ID is given encoded in the ``events`` table in the datastore, which also contains the realization associated
to the event. The properties of the rupture generating the events can be ascertained by looking inside the ``ruptures``
table. In particular ther ``srcidx`` contains the index of the source that generated the rupture. The ``srcidx`` can be
used to extract the properties of the sources by looking inside the ``source_info`` table, which contains the ``source_id``
string used in the XML source model.

************************************************
Can I run a calculation from a Jupyter notebook?
************************************************

You can run any kind of calculation from a Jupyter notebook, but usually calculations are long and it is not convenient
to run them interactively. Scenarios are an exception, since they are usually fast, unless you use spatial correlation
with a lot of sites. Assuming the parameters of the calculation are in a ``job.ini`` file you can run the following lines
in the notebook::

	In[1]: from openquake.calculators.base import run_calc
	In[2]: calc = run_calc('job.ini')

Then you can inspect the contents of the datastore and perform your postprocessing::

	In[3]: calc.datastore.open('r')  # open the datastore for reading

The inner format of the datastore is not guaranteed to be the same across releases and it is not documented, so this
approach is recommended to the most adventurous people.

***************************************************************
how do I plot/analyze/postprocess the results of a calculation?
***************************************************************

The official way to plot the result of a calculation is to use the `QGIS plugin <https://plugins.qgis.org/plugins/svir/>`_. There is also a command `oq plot` included with the engine distribution with some capabilities, please run

$ oq plot examples

to get the full list of available plots.

However you may want a kind of plot which is not available, or you may
want to batch-produce hundreds of plots, or you may want to plot the
results of a postprocessing operation. In such cases you need to use
the extract API and to write your own plotting/postprocessing code.

.. _faq-risk:

FAQ about running risk calculations
-----------------------------------

***********************************************************************************************
What implications do ``random_seed``, ``ses_seed``, and ``master_seed`` have on my calculation?
***********************************************************************************************

The OpenQuake engine uses (Monte Carlo) sampling strategies for propagating epistemic uncertainty at various stages in a
calculation. The sampling is based on numpy's pseudo-random number generator. Setting a 'seed' is useful for controlling
the initialization of the random number generator, and repeating a calculation using the same seed should result in
identical random numbers being generated each time.

Three different seeds are currently recognized and used by the OpenQuake engine.

- ``random_seed`` is the seed that controls the sampling of branches from both the source model logic tree and the ground motion model logic tree, when the parameter ``number_of_logic_tree_samples`` is non-zero. It affects both classical calculations and event based calculations.
- ``ses_seed`` is the seed that controls the sampling of the ruptures in an event based calculation (but notice that the generation of ruptures is also affected by the ``random_seed``, unless full enumeration of the logic tree is used, due to the reasons mentioned in the previous paragraph). It is also used to generate rupture seeds for both event based and scenario calculations, which are in turn used for sampling ground motion values / intensities from a Ground Motion Model, when the parameter ``truncation_level`` is non-zero. NB: before engine v3.11, sampling ground motion values / intensities from a GMM in a scenario calculation was incorrectly controlled by the ``random_seed`` and not the ``ses_seed``.
- ``master_seed`` is used when generating the epsilons in a calculation involving vulnerability functions with non-zero coefficients of variations. This is a purely risk-related seed, while the previous two are hazard-related seeds.

***************************************************************************************************************************************************************************************************************************
What values should I use for ``investigation_time``, ``ses_per_logic_tree_path``, and ``number_of_logic_tree_samples`` in my calculation? And what does the ``risk_investigation_time`` parameter for risk calculations do?
***************************************************************************************************************************************************************************************************************************

Setting the ``number_of_logic_tree_samples`` is relatively straightforward. This parameter controls the method used for
propagation of epistemic uncertainty represented in the logic-tree structure and calculation of statistics such as the
mean, median, and quantiles of key results.

``number_of_logic_tree_samples = 0`` implies that the engine will perform a so-called 'full-enumeration' of the
logic-tree, i.e., it will compute the requested results for every end-branch, or 'path' in the logic-tree. Statistics
are then computed with consideration of the relative weights assigned to each end-branch.

For models that have complex logic-trees containing thousands, or even millions of end-branches, a full-enumeration
calculation will be computationally infeasible. In such cases, a sampling strategy might be more preferable and much
more tractable. Setting, for instance, ``number_of_logic_tree_samples = 100`` implies that the engine will randomly
choose (i.e., 'sample') 100 end-branches from the complete logic-tree based on the weight assignments. The requested
results will be computed for each of these 100 sampled end-branches. Statistics are then computed using the results from
the 100 sampled end-branches, where the 100 sampled end-branches are considered to be equi-weighted (1/100 weight for each
sampled end-branch). Note that once the end-branches have been chosen for the calculation, the initial weights assigned
in the logic-tree files have no further role to play in the computation of the statistics of the requested results. As
mentioned in the previous section, changing the ``random_seed`` will result in a different set of paths or end-branches
being sampled.

The ``risk_investigation_time`` parameter is also fairly straightforward. It affects only the risk part of the computation
and does not affect the hazard calculations or results. Two of the most common risk metrics are (1) the time-averaged risk
value (damages, losses, fatalities) for a specified time-window, and (2) the risk values (damages, losses, fatalities)
corresponding to a set of return periods. The ``risk_investigation_time`` parameter controls the time-window used for
computing the former category of risk metrics. Specifically, setting ``risk_investigation_time = 1`` will produce average
annual risk values; such as average annual collapses, average annual losses, and average annual fatalities. This parameter
does not affect the computation of the latter category of risk metrics. For example, the loss exceedance curves will
remain the same irrespective of the value set for ``risk_investigation_time``, provided all other parameters are kept the
same.

Next, we come to the two parameters ``investigation_time`` and ``ses_per_logic_tree_path``.

If the hazard model includes time-dependent sources, the choice of the ``investigation_time`` will most likely be dictated
by the source model(s), and the engine will raise an error unless you set the value to that required by the source
model(s). In this case, the ``ses_per_logic_tree_path`` parameter can be used to control the effective length of the
stochastic event-set (or event catalog) for each end-branch, or 'path', for both full-enumeration and sampling-based
calculations. As an example, suppose that the hazard model requires you to set ``investigation_time = 1``, because the
source model defines 1-year occurrence probabilities for the seismic sources. Further, suppose you have decided to sample
100 branches from the complete logic-tree as your strategy to propagate epistemic uncertainty. Now, setting
``ses_per_logic_tree_path = 10000`` will imply that the engine will generate 10,000 'event-sets' for each of the 100
sampled branches, where each 'event-set' spans 1 year. Note that some of these 1-year event-sets could be empty, implying
that no events were generated in those particular 1-year intervals.

On the other hand, if the hazard model contains only time-independent sources, there is no hard constraint on the
``investigation_time`` parameter. In this case, the ``ses_per_logic_tree_path`` parameter can be used in conjunction with
the ``investigation_time`` to control the effective length of the stochastic event-set (or event catalog) for each
end-branch, or 'path', for both full-enumeration and sampling-based calculations. For instance, the following three
calculation settings would produce statistically equivalent risk results:

**Calculation 1**

::

	number_of_logic_tree_samples = 0
	investigation_time = 1
	ses_per_logic_tree_path = 10000
	risk_investigation_time = 1

**Calculation 2**

::

	number_of_logic_tree_samples = 0
	investigation_time = 50
	ses_per_logic_tree_path = 200
	risk_investigation_time = 1

**Calculation 3**

::

	number_of_logic_tree_samples = 0
	investigation_time = 10000
	ses_per_logic_tree_path = 1
	risk_investigation_time = 1

The effective catalog length per branch in such cases is ``investigation_time × ses_per_logic_tree_path``. The choice of
how to split the effective catalog length amongst the two parameters is up to the modeller/analyst's preferrence, and
there are no performance implications for perferring particular choices.

Note that if you were also computing hazard curves and maps in the above example calculations, the hazard curves output
in the first calculation would provide probabilities of exceedance in 1 year, whereas the hazard curves output in the
second calculation would provide probabilities of exceedance in 50 years. All **risk** results for the three calculations
will be statistically identical.

*************************************************************************
Why I am getting the warning "A big variation in the losses is expected"?
*************************************************************************

In event based risk calculations the warning means that your effective
investigation time is too small, you do not have enough events to have
sensible statistics and therefore your loss curves will strongly
depend on the choice of the `ses_seed`. The solution is to increase
the parameters `number_of_logic_tree_samples`,
`ses_per_logic_tree_path` or `investigation_time`.

The way the engine determines that the effective investigation time is
insufficient is to split the event IDs in two sets of odd and even
IDs.  If the number of relevant events is large, you expect the two
sets to be statistically equivalent and to produce very similar loss
curves; on the other hand, if you get the warning, it means that the
odd and even loss curves are quite different. Notice that the relevant
events are the ones corresponding to nonzero losses, therefore for
fatalities it is quite common to get the warning. In that case you can
accept that the precision on such curves is low and go on, since it
could be impractical to increase the effective investigation time (in
the sense that the calculation could get too slow or could even not
run due to out-of-memory/out-of-disk-space errors).

The command `oq show delta_loss:<loss_index>` displays the loss curves
for the odd and even sets of relevant events, so that you can get an idea
of the discrepancies. It is always available, even if the warning is
not displayed. The loss indexes corresponding to nonzero losses
can be extracted with the command::

  $ oq show loss_ids
  | loss_type     | loss_id |
  |---------------+---------|
  | nonstructural | 2       |
  | structural    | 3       |

For instance the even/odd loss curve for `nonstructural` can be displayed
as follows::

 $ oq show delta_loss:2
               loss          even           odd     delta
 5     9.794486e+07  8.659461e+07  1.026752e+08  0.084961
 10    2.627667e+08  2.463170e+08  2.913166e+08  0.083699
 20    5.115378e+08  5.389827e+08  5.060021e+08  0.031561
 50    9.174307e+08  9.665251e+08  8.286646e+08  0.076794
 100   1.214801e+09  1.126333e+09  1.305085e+09  0.073518
 200   2.018548e+09  1.718065e+09  2.063922e+09  0.091449
 500   3.366133e+09  2.235775e+09  5.022807e+09  0.383964
 1000  5.022807e+09  3.366133e+09  8.697419e+09  0.441933

That gives an indication of the error on the loss curve, which is normally
quite large. The `delta` is the relative error computed with the formula::

 delta = |loss_even - loss_odd| / (loss_even + loss_odd)

In many cases there is nothing you can do about that since
the statistical error goes down with `1 / sqrt(num_events)` and therefore
it requires a quadratic effort to reduce it (i.e. 100 times more
computations only reduce the error 10 times).

In scenario risk calculations there are no loss curves, however you can
still get the same warning if the average losses (averaged over the number
of events) are quite different between odd and even events. In that case
you can get something as follows::

  $ oq show delta_loss:1
             even           odd     delta
  0  5.242724e+09  5.175095e+09  0.006492
  1  4.857120e+09  5.470883e+09  0.059427

where the index correspond to the realization index (i.e. the GSIM).

***************************************
Can I disaggregate my losses by source?
***************************************

Starting from engine v3.10 you can get a summary of the total losses across your portfolio of assets arising from each
seismic source, over the effective investigation time. For instance run the event based risk demo as follows::

	$ oq engine --run job.ini

and export the output "Source Loss Table". You should see a table like the one below:

+------------+---------------+----------------+
| **source** | **loss_type** | **loss_value** |
+============+===============+================+
|    231     | nonstructural |  1.07658E+10   |
+------------+---------------+----------------+
|    231     |  structural   |  1.63773E+10   |
+------------+---------------+----------------+
|    386     | nonstructural |  3.82246E+07   |
+------------+---------------+----------------+
|    386     |  structural   |  6.18172E+07   |
+------------+---------------+----------------+
|    238     | nonstructural |  2.75016E+08   |
+------------+---------------+----------------+
|    238     |  structural   |  4.58682E+08   |
+------------+---------------+----------------+
|    239     | nonstructural |  4.51321E+05   |
+------------+---------------+----------------+
|    239     |  structural   |  7.62048E+05   |
+------------+---------------+----------------+
|    240     | nonstructural |  9.49753E+04   |
+------------+---------------+----------------+
|    240     |  structural   |  1.58884E+05   |
+------------+---------------+----------------+
|    280     | nonstructural |  6.44677E+03   |
+------------+---------------+----------------+
|    280     |  structural   |  1.14898E+04   |
+------------+---------------+----------------+
|    374     | nonstructural |  8.14875E+07   |
+------------+---------------+----------------+
|    374     |  structural   |  1.35158E+08   |
+------------+---------------+----------------+
|     ⋮      |       ⋮       |        ⋮       |
+------------+---------------+----------------+

from which one can infer the sources causing the highest total losses for the portfolio of assets within the specified
effective investigation time.

*************************************************************************
How does the engine compute loss curves (a.k.a. Probable Maximum Losses)?
*************************************************************************

The PML for a given return period is built from the losses in the event loss table. The algorithm used is documented in
detail in the advanced manual at the end of the section about risk calculations. The section also explains why sometimes
the PML or the loss curves contain NaN values (the effective investigation time is too short compared to the return
period). Finally, it also explains why the PML is not additive.

.. _faq-cluster:

FAQ related to cluster deployments
----------------------------------

***************************************************************************
What it is the proper way to install the engine on a supercomputer cluster?
***************************************************************************

Normally a supercomputer cluster cannot be fully assigned to the OpenQuake engine, so you cannot perform the :ref:`regular
cluster installation <cluster>`. We suggest to do the following instead:

- install the engine in server mode on the machine that will host the database and set ``shared_dir=/opt/openquake`` in the openquake.cfg file; such machine can have low specs; optionally, you can run the WebUI there, so that the users can easily download the results
- expose /opt/openquake to all the machines in the cluster by using a read-write shared filesystem
- then run the calculations on the other cluster nodes; the outputs will be saved in /opt/openquake/oqdata and the code will be read from /opt/openquake/venv; this will work if all the nodes have a vanilla python installation consistent with the one on the database machine.

*********************************************
Recover after a Out Of Memory (OOM) condition
*********************************************

When an Out Of Memory (OOM) condition occours on the master node the ``oq`` process is terminated by the operating system
OOM killer via a ``SIGKILL`` signal.

Due to the forcefully termination of ``oq``, processes may be left running, using resources (both CPU and RAM), until
the task execution reaches an end.

To free up resources for a new run **you must kill all openquake processes on the workers nodes**; this will stop any
other running computation which is anyway highly probable to be already broken due to the OOM condition on the master
node.

***********************************
error: OSError: Unable to open file
***********************************

A more detailed stack trace::

	OSError:
	  File "/opt/openquake/lib/python3.8/site-packages/openquake/baselib/parallel.py", line 312, in new
	    val = func(*args)
	  File "/opt/openquake/lib/python3.8/site-packages/openquake/baselib/parallel.py", line 376, in gfunc
	    yield func(*args)
	  File "/opt/openquake/lib/python3.8/site-packages/openquake/calculators/classical.py", line 301, in build_hazard_stats
	    pgetter.init()  # if not already initialized
	  File "/opt/openquake/lib/python3.8/site-packages/openquake/calculators/getters.py", line 69, in init
	    self.dstore = hdf5.File(self.dstore, 'r')
	  File "/opt/openquake/lib64/python3.8/site-packages/h5py/_hl/files.py", line 312, in __init__
	    fid = make_fid(name, mode, userblock_size, fapl, swmr=swmr)
	  File "/opt/openquake/lib64/python3.8/site-packages/h5py/_hl/files.py", line 142, in make_fid
	    fid = h5f.open(name, flags, fapl=fapl)
	  File "h5py/_objects.pyx", line 54, in h5py._objects.with_phil.wrapper
	  File "h5py/_objects.pyx", line 55, in h5py._objects.with_phil.wrapper
	  File "h5py/h5f.pyx", line 78, in h5py.h5f.open
	OSError: Unable to open file (unable to open file: name = '/home/openquake/oqdata/cache_1.hdf5', errno = 2, error message = 'No such file or directory', flags = 0, o_flags = 0)

This happens when the :ref:`shared dir <cluster>`
is not configured properly and workers cannot access data from the master node. Please note that starting with OpenQuake
engine 3.3 the shared directory is required on multi-node deployments.

You can get more information about setting up the shared directory on the :ref:`cluster installation page <cluster>`.

-------

********
Get help
********

If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake engine users mailing list:
https://groups.google.com/g/openquake-users
