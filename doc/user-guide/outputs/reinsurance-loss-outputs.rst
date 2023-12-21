Reinsurance Loss Outputs
========================

The reinsurance calculations generates estimates of retention and cession under the different
reinsurance treaties. The following output files are produced:

1. ``Reinsurance by event``: aggregated estimated per event for the claim, retention, 
   cession and overspills under each reinsurance treaty.

   +----------+-----------+---------+----------+----------+---------+--------------------+------+
   | event_id | retention | claim   | treaty_1 | treaty_2 | xlr1    | overspill_treaty_2 | year |
   +==========+===========+=========+==========+==========+=========+====================+======+
   | 0        | 738.429   | 1833.73 | 142.206  | 400.000  | 553.096 | 180.819            | 1    |
   +----------+-----------+---------+----------+----------+---------+--------------------+------+
   | 1        | 319.755   | 701.219 | 51.7092  | 179.292  | 150.463 | 0.00000            | 1    |
   +----------+-----------+---------+----------+----------+---------+--------------------+------+
   | 2        | 1226.97   | 3210.91 | 282.622  | 400.000  | 1301.32 | 474.357            | 1    |
   +----------+-----------+---------+----------+----------+---------+--------------------+------+
   | 3        | 1318.88   | 3600.81 | 294.502  | 400.000  | 1587.42 | 629.187            | 1    |
   +----------+-----------+---------+----------+----------+---------+--------------------+------+

2. ``Reinsurance curves``: reinsurance loss exceedance curves describe the probabilities
   of exceeding a set of loss ratios or loss values, within a given time span 
   (or investigation interval). The curves are generated for the claim, retention, 
   cession and overspills under each reinsurance treaty.

   +--------+---------------+-----------+---------+----------+----------+---------+--------------------+
   | rlz_id | return_period | retention | claim   | treaty_1 | treaty_2 | xlr1    | overspill_treaty_2 |
   +========+===============+===========+=========+==========+==========+=========+====================+
   | 0      | 50.0000       | 319.755   | 701.219 | 51.7092  | 179.292  | 150.463 | 0.00000            |
   +--------+---------------+-----------+---------+----------+----------+---------+--------------------+
   | 0      | 100.000       | 1226.97   | 3210.91 | 282.622  | 400.000  | 1301.32 | 474.357            |
   +--------+---------------+-----------+---------+----------+----------+---------+--------------------+
   | 0      | 200.000       | 1318.88   | 3600.81 | 294.502  | 400.000  | 1587.42 | 629.187            |
   +--------+---------------+-----------+---------+----------+----------+---------+--------------------+

3. ``Average reinsurance losses``: the average reinsurance losses
   indicates the expected value within the time period specified
   by risk_investigation_time for the claim, retention, and
   cessions under each reinsurance treaty for all policies in the
   Exposure Model.

   +--------+-------------+-------------+-------------+-------------+-------------+--------------------+
   | rlz_id | retention   | claim       | treaty_1    | treaty_2    | xlr1        | overspill_treaty_2 |
   +========+=============+=============+=============+=============+=============+====================+
   | 0      | 1.80202E+01 | 4.67333E+01 | 3.85520E+00 | 6.89646E+00 | 1.79615E+01 | 6.42181E+00        |
   +--------+-------------+-------------+-------------+-------------+-------------+--------------------+

4. ``Aggregated reinsurance by policy``:  the average reinsurance losses
   for each policy, by ignoring the overspill logic.

   +--------+-----------+-----------+---------+----------+----------+----------+
   | rlz_id | policy_id | retention | claim   | treaty_1 | treaty_2 | xlr1     |
   +========+===========+===========+=========+==========+==========+==========+
   | 0      | p1_a1     | 4.61304   | 19.0934 | 1.90934  | 3.81867  | 8.75232  |
   +--------+-----------+-----------+---------+----------+----------+----------+
   | 0      | p1_a2     | 3.01643   | 6.48621 | 1.94586  | 0.648621 | 0.875298 |
   +--------+-----------+-----------+---------+----------+----------+----------+
   | 0      | p1_a3     | 38.9468   | 1.29823 | 0.00000  | 0.908759 | 0.00000  |
   +--------+-----------+-----------+---------+----------+----------+----------+
   | 0      | p2        | 3.57945   | 19.8555 | 0.00000  | 7.94221  | 8.33388  |
   +--------+-----------+-----------+---------+----------+----------+----------+

The parameters indicated in the previous outputs include:

- ``policy``: identifier of the unique policies indicated in the
  exposure model and policy files.

- ``claim``: ground up losses minus the deductible and up to the policy liability.

- ``retention``: net losses that the insurance company keeps for its own account.

- ``cession_i``: net losses that are ceded by the insurance company to
  the reinsurer(s) under treaty i. The cession is indicated by the
  treaty name defined in the reinsurance information.

- ``overspill_treaty_i``: net losses that exceed the maximum cession
  per event ("max_cession_event") for *proportional* and/or *catxl*
  treaties.

*NOTE: The sum of the claim is not equal to the ground up losses, since
usually the deductible is nonzero. Moreover there could be
"non-insured" losses corresponding to policies with no insurance
contracts or that exceed the policy liability.*