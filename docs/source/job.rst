..
      License Header goes here

Jobs
====
Super job type happy stuff
--------------------------


A Job is an object responsible for parsing a configuration, loading the appropriate behaviour based on that configuration, and then executing the tasks associated with that behaviour. The workflow of a Job is broken up into four parts: the Job class, the Mixin class, the Risk and Hazard mixin proxies, and the various Hazard and Risk mixins to define behaviour.


The :mod:`job` class
--------------------
.. automodule:: openquake.job
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`mixin` class
----------------------
.. automodule:: openquake.job.mixins
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`hazard` job proxy and mixins
--------------------------------------
.. automodule:: openquake.hazard.job
    :members:
    :undoc-members:
    :show-inheritance:

The :mod:`risk` job proxy and mixins
------------------------------------
.. automodule:: openquake.risk.job
    :members:
    :undoc-members:
    :show-inheritance:
.. automodule:: openquake.risk.job.deterministic
    :members:
    :undoc-members:
    :show-inheritance:
