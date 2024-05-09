.. _reinsurance:

Reinsurance
===========

To run reinsurance calculations, in addition to the required files for performing event-based or scenario risk calculations, it is required to adjust the exposure information, and to include two additional files:

1. Reinsurance information: an ``.xml`` file defining the characteristics of the reinsurance treaties (e.g., “reinsurance.xml”).
2. Policy information: a ``.csv`` file with details of each policy indicated in the exposure model and the associated reinsurance treaties (e.g., “policy.csv”).

The insurance information includes the allocation of assets into a given policy, the liability and the deductible. The deductible can be defined at asset level (therefore indicated in the exposure model ``csv`` file), or in at the policy level (therefore indicated in the policy ``csv`` file). The current implementation only supports liability at policy level.


Exposure file
-------------

The exposure input file (csv and xml with metadata) needs to be adjusted to include a ``policy`` tag that indicates the type of policy (and therefore the reinsurance contracts) associated with each asset.

Policies can be defined for single or multiple assets. When multiple assets are allocated to the same policy, losses are aggregated at the policy level before applying the insurance and reinsurance deductions.

Below we present an example of an exposure model considering the policy information and its associated metadata:

``exposure_model.csv``

+--------+-----------+---------+--------------+------------+----------------+--------------+-------------------+---------------------------+-----------+-----------+------------+
| **id** |  **lon**  | **lat** | **taxonomy** | **number** | **structural** | **contents** | **nonstructural** | **business_interruption** | **night** | **tag_1** | **policy** |
+========+===========+=========+==============+============+================+==============+===================+===========================+===========+===========+============+
|   a1   |   -122    | 38.113  |     tax1     |      1     |      10000     |     5000     |       15000       |            2000           |     6     |   zone_1  |    p1_a1   |
+--------+-----------+---------+--------------+------------+----------------+--------------+-------------------+---------------------------+-----------+-----------+------------+
|   a2   | -122.114  | 38.113  |     tax1     |      1     |      10000     |     5000     |       15000       |            2000           |     6     |   zone_1  |    p1_a2   |
+--------+-----------+---------+--------------+------------+----------------+--------------+-------------------+---------------------------+-----------+-----------+------------+
|   a3   |  -122.57  | 38.113  |     tax1     |      1     |      10000     |     5000     |       15000       |            2000           |     6     |   zone_1  |    p1_a3   |
+--------+-----------+---------+--------------+------------+----------------+--------------+-------------------+---------------------------+-----------+-----------+------------+
|   a4   |    -122   |    38   |     tax1     |      1     |      10000     |     5000     |       15000       |            2000           |     6     |   zone_2  |     p2     |
+--------+-----------+---------+--------------+------------+----------------+--------------+-------------------+---------------------------+-----------+-----------+------------+
|   a5   |    -122   |  37.91  |     tax1     |      1     |      10000     |     5000     |       15000       |            2000           |     6     |   zone_2  |     p2     |
+--------+-----------+---------+--------------+------------+----------------+--------------+-------------------+---------------------------+-----------+-----------+------------+
|   a6   |    -122   | 38.225  |     tax1     |      1     |      10000     |     5000     |       15000       |            2000           |     6     |   zone_2  |     p2     |
+--------+-----------+---------+--------------+------------+----------------+--------------+-------------------+---------------------------+-----------+-----------+------------+
|   a7   |  -121.886 | 38.113  |     tax1     |      1     |      10000     |     5000     |       15000       |            2000           |     6     |   zone_2  |     p2     |
+--------+-----------+---------+--------------+------------+----------------+--------------+-------------------+---------------------------+-----------+-----------+------------+

``exposure.xml``

::

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
	  <exposureModel id="ex1" category="buildings" taxonomySource="GEM taxonomy">
	    <description>exposure model</description>
	    <conversions>
	      <costTypes>
	        <costType name="structural" type="aggregated" unit="USD"/>
	        <costType name="nonstructural" type="aggregated" unit="USD"/>
	        <costType name="contents" type="aggregated" unit="USD"/>
	      </costTypes>
	    </conversions>
	    <tagNames>tag_1 policy</tagNames>
	    <occupancyPeriods>night </occupancyPeriods>
	    <assets>
	      exposure_model.csv
	    </assets>
	  </exposureModel>
	</nrml>

This example presents 7 assets (a1 to a7) with 4 associated policies. Notice that the column ``policy`` is mandatory, as well as the line ``<tagNames>policy</tagNames>`` in the xml. Additional tags can be included as needed.

Starting from OpenQuake engine v3.17, the exposure module can also include deductibles at asset level (called ``ideductible``). In this case, the deductions are applied at asset level, and later aggregated at the policy level before applying the liability and reinsurance allocations.

NOTE: It is not possible to have a policy with ``ideductible`` at asset and ``deductible`` at policy level. The engine only accepts one value.

Insurance and reinsurance information (``reinsurance.xml``)
-----------------------------------------------------------
The insurance and reinsurance information is defined by a ``reinsurance.xml`` that includes the metadata and treaty characteristics for each treaty specified in the policy information.

The following example facilitates the understanding of the input file::

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"
	      xmlns:gml="http://www.opengis.net/gml">
	  <reinsuranceModel>
	    <description>reinsurance model</description>
	
	    <fieldMap>
	      <field oq="liability" input="Limit" />
	      <field oq="deductible" input="Deductible" />
	
	      <field input="treaty_1" type="prop" max_cession_event="400" />
	      <field input="treaty_2" type="prop" max_cession_event="400" />
	      <field input="xlr1" type="wxlr" deductible="200" limit="1000" />
	    </fieldMap>
	  <policies>policy.csv</policies>
	  </reinsuranceModel>
	</nrml>

**reinsurance.xml parameters:**

The reinsurance information must include, at least, a ``<description>`` and a list of files that contain the ``<policies>``. The ``<fieldMap>`` block is used to define the reinsurance treaties and their parameters.

The ``oq`` and ``input`` parameters are used to specify the *key* used in the engine (``oq``) and its equivalent column header in the policy file (``input``). All reinsurance calculations must include, at least, the insurance characteristics of each policy: liability and deductible (that can be at asset or policy level, depending on the portfolio characteristics). Then, the definition of reinsurance treaties depends on the treaty type: proportional or non proportional.

Proportional treaties are identified by the parameter ``type="prop"``. The fraction of losses ceded to each treaty is specified for each policy covered by the treaty, and the retention is calculated as 1 minus all the fractions specified in the multiple layers of proportional treaties. For each proportional treaty it is possible to define the ``max_cession_event``. The most common types of proportional treaties are “Quota Share” and “Surplus”.

Non-proportional treaties are identified by the parameter ``type="wxlr"`` or ``type="catxl"``. For each treaty it is required to indicate the ``deductible`` and ``limit``.

Note: treaties must be written in a given order, keeping proportional ones first, then non-proportional ones of type “wxlr” and finally those of type “catxl”.

- **insurance deductible**: the amount (economic value) that the insurer will “deduct” from the ground up losses before paying up to its policy limits. The units of the deductible must be compatible with the units indicated in the exposure model (e.g. USD dollars or Euros). The deductible can be specified at policy (``deductible``) or asset level (``ideductible``) depending on the insurance contract.

  The claim is calculated as ``claim = ground_up_loss - deductible`` for policies with deductibles defined at the policy level, or ``claim = ground_up_loss - ideductible`` for policies with deductibles defined at the asset level.

- **insurance liability**: the maximum economic amount that can be covered by the insurance, according to the policy characteristics. The liability is also known as limit or maximum coverage.
- **type**: parameter that specifies the type of treaty. There are three supported types: ``prop`` (for proportional treaties), ``wxlr``, or ``catxl``.
- **max_cession_event**: the maximum cession per event is an optional parameter for proportional reinsurance treaties. It refers to the maximum cession accepted by the reinsurance company for the aggregated losses produced by a single event. If the aggregated losses exceed this threshold, then the cession in excess is reported as an ``overspill``.
- **reinsurance deductible**: only applicable to non-proportional treaties, the maximum retention (also known as “first loss”) is the limit above which the reinsurer becomes liable for losses up to the upper limit of cover.
- **reinsurance limit**: in non-proportional treaties it refers to the upper limit of cover or ceiling. The reinsurance_cover is the amount between the ``deductible`` (deductible) and the upper limit of cover.

Note: the current engine implementation does not support an “annual aggregate limit” for non-proportional reinsurance treaties.

Policy information (``policy.csv``)
-----------------------------------

The policy input file indicates, for each policy, the insurance values (deductible and liability), as well as the reinsurance contracts associated with each policy present in the exposure model.

For **proportional** treaties, the values indicated in each columns refer to the fraction of cession under the reinsurance treaty. On the other hand, for **non-proportional** treaties, the values are indicates as 1 for policies covered within the treaty and zero when they are not part of the treaty.

The table below presents an example of the four policies indicated in the example of the exposure model and the reinsurance presented above:

``policy.csv``

+------------+-------------+----------------+--------------+--------------+-----------+
| **policy** |  **Limit**  | **Deductible** | **treaty_1** | **treaty_2** | **xlr_1** |
+============+=============+================+==============+==============+===========+
|    p1_a1   |     2000    |       400      |      0.1     |      0.2     |     1     |
+------------+-------------+----------------+--------------+--------------+-----------+
|    p1_a2   |     1000    |       200      |      0.3     |      0.1     |     1     |
+------------+-------------+----------------+--------------+--------------+-----------+
|    p1_a3   |     1000    |       100      |       0      |      0.7     |     1     |
+------------+-------------+----------------+--------------+--------------+-----------+
|     p2     |     2000    |       500      |       0      |      0.4     |     1     |
+------------+-------------+----------------+--------------+--------------+-----------+

The ``policy`` column must contain the same identifiers as the ones specified by the ``policy`` field in the exposure model.

In this example the ``Limit`` corresponds to the ``liability`` of each policy, while the ``Deductible`` refers to the ``deductible`` in the engine. Both columns indicate the absolute values using the same units as the exposed values in the exposure model. There are two proportional reinsurance treaties (namely ``treaty_1`` and ``treaty_2``), and the values indicated in each column represent the fraction of cession under each treaty. For example, for “p1_a1” the “treaty_1” ceeds 0.1 of the losses and there is a cession of 0.2 under the “treaty_2”; therefore the retention corresponding to the proportional treaties for “p1_a1” will be (1 - 0.1 - 0.2 = 0.7). In the case of non-proportional treaties, “p1_a1” is allocated to the xlr1 (an excess of loss per risk) treaty. This policy is not covered by the ``catxl`` treaties.

Note: treaties must be written in a given order, keeping proportional ones first, then non-proportional ones of type “wxlr” and finally those of type “catxl”.