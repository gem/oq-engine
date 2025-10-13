Reinsurance
-----------

Reinsurance losses can be calculated for event-based and scenario risk calculations. To do so, the configuration file, 
``job.ini``, needs to specify the parameters presented below, in addition to the parameters generally indicated for these 
type of calculations::

	[risk_calculation]
	aggregate_by = policy
	reinsurance_file = {'structural+contents': 'reinsurance.xml'}
	total_losses = structural+contents

**Additional comments:**

- ``aggregate_by``: it is possible to define multiple aggregation keys. However, for reinsurance calculations the ``policy`` key must be present, otherwise an error message will be raised. In the following example, multiple aggregation keys are used::

	aggregate_by = policy; tag1

  In this case, aggregated loss curves will be produced also for ``tag1`` and ``policy``, while reinsurance outputs will only be produced for the policy.

- ``reinsurance_file``: This dictionary associates the reinsurance information to a given the loss_type (the engine supports structural, nonstructural, contents or its sum). The insurance and reinsurance calculations are applied over the indicated loss_types, i.e. to the sum of the ground up losses associated with the specified loss_types.

  *NOTE: The current implementation works only with a single reinsurance file.*

- ``total_losses``: (or total exposed value) needs to be specified when the reinsurance needs to be applied over the sum of two or more loss types (e.g. ``structural+contents``). The definition of total losses is also reflected in the risk outputs of the calculation. NB: if there is a single loss type (e.g. ``structural``) there is no need to specify this parameter, just write ``reinsurance_file = {'structural': 'reinsurance.xml'}``
