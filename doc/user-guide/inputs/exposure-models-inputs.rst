.. _exposure-models:

Exposure Models
===============

All risk calculators in the OpenQuake engine require an *Exposure Model* that needs to be provided in the Natural hazards’ 
Risk Markup Language schema, the use of which is illustrated through several examples in this section. The information 
included in an *Exposure Model* comprises a metadata section listing general information about the exposure, followed by 
a cost conversions section that describes how the different areas, costs, and occupancies for the assets will be specified, 
followed by data regarding each individual asset in the portfolio.

**Note**: Starting from OpenQuake engine v3.0, the *Exposure Model* may be provided using csv files listing the asset 
information, along with an xml file containing the metadata section for the exposure model that is described in the 
examples below.


Exposure information
--------------------

A simple *Exposure Model Metadata XML* is shown in the listing below:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>Exposure Model Example</description>
	
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="per_area" unit="USD" />
	    </costTypes>
	    <area type="per_asset" unit="SQM" />
	  </conversions>

	<occupancyPeriods>night</occupancyPeriods>
	<tagNames>OCCUPANCY NAME_1 ID_1 NAME_2 ID_2</tagNames>
	<assets>Exposure_File_1.csv Exposure_File_2.csv Exposure_File_3.csv </assets>

	<exposureFields>
		<field oq="taxonomy" input="TAXONOMY" />
		<field oq="number" input="BUILDINGS" />
		<field oq="area" input="AREA_PER_DWELLING_SQM" />
		<field oq="value" type="structural" input="COST_PER_AREA_USD" />
		<field oq="value" type="nonstructural" input="COST_NONSTRUCTURAL_USD" />
		<field oq="night" input="OCCUPANTS_PER_ASSET" />
	</exposureFields>

	</exposureModel>
		
	</nrml>

Let us take a look at each of the sections in the above example file.
There are 5 main sections:
- general info
- conversions
- occupancyPeriods
- tagNames
- assets

An additional section, ``exposureFields``, can be included when the asset information is provided in CSV format.

************
general info
************

The general information section in the metadata XML provides an overview of the characteristics of the exposure model,
is common to all of the assets in the portfolio, and needs to be incorporated at 
the beginning of every *Exposure Model XML* file. There are a number of parameters that compose the general info section,
which is intended to provide general information regarding the assets within the *Exposure Model*. 
These parameters are described below:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>Exposure Model Example</description>

- ``id``: mandatory; a unique string used to identify the *Exposure Model*. This string can contain letters (a–z; A–Z), numbers (0–9), dashes (–), and underscores (_), with a maximum of 100 characters.
- ``category``: an optional string used to define the type of assets being stored (e.g: buildings, lifelines).
- ``taxonomySource``: an optional attribute used to define the taxonomy being used to classify the assets.
- ``description``: mandatory; a brief string (ASCII) with further information about the *Exposure Model*.


***********
conversions
***********

The `conversions` section is common to all of the assets in the portfolio and needs to be incorporated in the *Exposure Model XML* file.
This section describes the area and cost conversions applied to all assets in the exposure model.

.. code-block:: xml

	  <conversions>
	    <costTypes>
	      <costType name="structural" type="per_area" unit="USD" />
	    </costTypes>
	    <area type="per_asset" unit="SQM" />
	  </conversions>


Notice that the ``costType`` element defines a ``name``, a ``type``, and a ``unit`` attribute.

The Natural hazards’ Risk Markup Language schema for the *Exposure Model* allows the definition of a structural cost, a 
nonstructural components cost, a contents cost, and a business interruption or downtime cost for each asset in the 
portfolio. Thus, the valid values for the ``name`` attribute of the ``costType`` element are the following:

- ``structural``: used to specify the structural replacement cost of assets
- ``nonstructural``: used to specify the replacement cost for the nonstructural components of assets
- ``contents``: used to specify the contents replacement cost
- ``business_interruption``: used to specify the cost that will be incurred per unit time that a damaged asset remains closed following an earthquake

The *Exposure Model* shown in the example above defines only the structural values for the assets. However, multiple 
cost types can be defined for each asset in the same *Exposure Model*.

The ``unit`` attribute of the ``costType`` element is used for specifying the currency unit for the corresponding cost 
type. Note that the OpenQuake engine itself is agnostic to the currency units; the ``unit`` is thus a descriptive 
attribute which is used by the OpenQuake engine to annotate the results of a risk assessment. This attribute can be set 
to any valid Unicode string.

The ``type`` attribute of the ``costType`` element specifies whether the costs will be provided as an aggregated value 
for an asset, or per building or unit comprising an asset, or per unit area of an asset. The valid values for the ``type`` 
attribute of the ``costType`` element are the following:

- ``aggregated``: indicates that the replacement costs will be provided as an aggregated value for each asset
- ``per_asset``: indicates that the replacement costs will be provided per structural unit comprising each asset
- ``per_area``: indicates that the replacement costs will be provided per unit area for each asset

If the costs are to be specified ``per_area`` for any of the ``costTypes``, the ``area`` element will also need to be 
defined in the conversions section. The ``area`` element defines a ``type``, and a ``unit`` attribute.

The ``unit`` attribute of the ``area`` element is used for specifying the units for the area of an asset. The OpenQuake 
engine itself is agnostic to the area units; the ``unit`` is thus a descriptive attribute which is used by the OpenQuake 
engine to annotate the results of a risk assessment. This attribute can be set to any valid ASCII string.

The ``type`` attribute of the ``area`` element specifies whether the area will be provided as an aggregated value for an 
asset, or per building or unit comprising an asset. The valid values for the ``type`` attribute of the ``area`` element 
are the following:

- ``aggregated``: indicates that the area will be provided as an aggregated value for each asset
- ``per_asset``: indicates that the area will be provided per building or unit comprising each asset

The way the information about the characteristics of the assets in an *Exposure Model* are stored can vary strongly 
depending on how and why the data was compiled. As an example, if national census information is used to estimated the 
distribution of assets in a given region, it is likely that the number of buildings within a given geographical area 
will be used to define the dataset, and will be used for estimating the number of collapsed buildings for a scenario 
earthquake. On the other hand, if simplified methodologies based on proxy data such as population distribution are used 
to develop the *Exposure Model*, then it is likely that the built up area or economic cost of each building typology will 
be directly derived, and will be used for the estimation of economic losses.

**benefit/cost assessment**

In order to perform a benefit/cost assessment, it is necessary to indicate the retrofitting cost. This parameter is 
handled in the same manner as the structural cost, and it should be stored according to the format shown in the listing 
below:

.. code-block:: xml

	  <conversions>
	    <costTypes>
	      <costType name="structural" type="aggregated" unit="USD"
	                retrofittedType="per_asset" retrofittedUnit="USD" />
	    </costTypes>
	    <area type="per_asset" unit="SQM" />
	  </conversions>

Despite the fact that for the demonstration of how the retrofitting cost can be stored the "per_asset" type of cost 
structure was used, it is important to mention that any of the other cost storing approaches can 
also be employed.


****************
occupancyPeriods
****************

The OpenQuake engine is also capable of estimating human losses based on the number of occupants in an asset, at a 
certain time of the day. The `occupancyPeriods` section is common to all of the assets in the portfolio. 
This section is only required for probabilistic or scenario calculations that specify an ``occupants_vulnerability_file``. 

Each entry within this element specifies the number of occupants for the asset for a particular period of the day. 

.. code-block:: xml

	<occupancyPeriods>night</occupancyPeriods>

As shown in the example above, each occupancy entry must define the ``period`` and the ``occupants``. 
Currently supported valid options for the ``period`` are: ``day``, ``transit``, and ``night``. 
Currently, the number of ``occupants`` for an asset can only be provided as an aggregated value for the asset.


********
tagNames
********

Starting from OpenQuake engine v2.7, the user may also provide a set of tags for each asset in the *Exposure Model*. The 
primary intended use case for the tags is to enable aggregation or accumulation of risk results (casualties / damages / 
losses) for each tag. The tags could be used to specify location attributes, occupancy types, or insurance policy codes 
for the different assets in the *Exposure Model*.

.. code-block:: xml

	<tagNames>OCCUPANCY NAME_1 ID_1 NAME_2 ID_2</tagNames>

Note that it is not mandatory that every tag name specified in the metadata section must be provided with a tag value 
for each asset.


******
assets
******

The `assets` section is the part of the file describing the set of assets in the portfolio to be used in seismic damage 
or risk calculations.

Each asset definition involves specifying a set of mandatory and optional attributes concerning the asset. The following 
set of attributes can be assigned to each asset based on the current schema for the *Exposure Model*:

- ``id``: mandatory; a unique string used to identify the given asset, which is used by the OpenQuake engine to relate each asset with its associated results. This string can contain letters (a–z; A–Z), numbers (0–9), dashes (-), and underscores (_), with a maximum of 100 characters.
- ``taxonomy``: mandatory; this string specifies the building typology of the given asset. The taxonomy strings can be user-defined, or based on an existing classification scheme such as the GEM Taxonomy, PAGER, or EMS-98.
- ``number``: the number of individual structural units comprising a given asset. This attribute is mandatory for damage calculations. For risk calculations, this attribute must be defined if either the area or any of the costs are provided per structural unit comprising each asset.
- ``area``: area of the asset, at a given location. As mentioned earlier, the area is a mandatory attribute only if any one of the costs for the asset is specified per unit area.
- ``location``: mandatory; specifies the longitude (between -180 degrees to 180 degrees) and latitude (between -90 degrees to 90 degrees) of the given asset, both specified in decimal degrees [1]_.
- ``costs``: specifies a set of costs for the given asset. The replacement value for different cost types must be provided on separate lines within the ``costs`` element. As shown in the example above, each cost entry must define the ``type`` and the ``value``. Currently supported valid options for the cost ``type`` are: ``structural``, ``nonstructural``, ``contents``, and ``business_interruption``.
- ``occupancies``: mandatory only for probabilistic or scenario risk calculations that specify an ``occupants_vulnerability_file``. Each entry within this element specifies the number of occupants for the asset for a particular period of the day. As shown in the example above, each occupancy entry must define the ``period`` and the ``occupants``. Currently supported valid options for the ``period`` are: ``day``, ``transit``, and ``night``. Currently, the number of ``occupants`` for an asset can only be provided as an aggregated value for the asset.

For the purposes of performing a retrofitting benefit/cost analysis, it is also necessary to define the retrofitting 
cost (``retrofitted``). The combination between the possible options in which these three attributes can be defined leads 
to four ways of storing the information about the assets. For each of these cases a brief explanation and example is 
provided in this section.


The asset information in an *Exposure Model* can be provided in different formats, depending on the level of detail and the structure of the data. Below are examples of how to include asset information using the available formats.

1. **XML Format**: Asset information can be directly embedded in the XML file, as shown in the examples above. Each asset is defined with attributes such as `id`, `taxonomy`, `location`, `costs`, and optionally `occupancies` and `tags`.

2. **CSV Format**: Asset information can also be provided in one or more CSV files, with the metadata section referencing these files. This approach is useful for large datasets. The CSV files must include headers that match the expected attributes, such as `id`, `lon`, `lat`, `taxonomy`, `number`, `structural`, `area`, and others.


**************
exposureFields
**************

It is common for exposure models to include more information than what is strictly required for running a risk calculation in OpenQuake. 
Additionally, the headers in exposure files often vary depending on the modeller's preferences, language, or conventions 
(e.g., the field `night` might be labeled as `occupants_night` or `population_at_night`).

This flexibility is only relevant for input models in `.csv` format. To accommodate this, 
OpenQuake provides a mechanism for mapping custom CSV headers to the required OpenQuake fields.
This allows users to define a flexible structure for their CSV files while ensuring compatibility with OpenQuake's requirements.

The example below demonstrates how custom headers in a `.csv` file can be mapped to the corresponding OpenQuake attributes:

.. code-block:: xml

	<assets>Exposure_File_1.csv Exposure_File_2.csv Exposure_File_3.csv </assets>

	<exposureFields>
		<field oq="taxonomy" input="TAXONOMY" />
		<field oq="number" input="BUILDINGS" />
		<field oq="area" input="AREA_PER_DWELLING_SQM" />
		<field oq="value" type="structural" input="COST_PER_AREA_USD" />
		<field oq="value" type="nonstructural" input="COST_NONSTRUCTURAL_USD" />
		<field oq="night" input="OCCUPANTS_PER_ASSET" />
	</exposureFields>



Exposure model in CSV format
----------------------------

A combination of XML and CSV formats can be used, where the metadata is defined in XML and the asset data is stored in CSV files. This allows for flexibility and scalability.

**************
Example `.csv`
**************

This example illustrates the use of multiple csv files containing the assets information, in conjunction with the 
metadata section in the usual xml format.

Let us take a look at the metadata section of the Exposure Model, which is listed as usual in an xml file:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example_with_csv_files"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.0">
	  <description>Exposure Model Example with CSV Files</description>
	
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="aggregated" unit="USD" />
	      <costType name="nonstructural" type="aggregated" unit="USD" />
	      <costType name="contents" type="aggregated" unit="USD" />
	    </costTypes>
	    <area type="per_asset" unit="SQFT" />
	  </conversions>
	
	  <occupancyPeriods>night</occupancyPeriods>
	
	  <tagNames>occupancy state_id state county_id county tract</tagNames>
	
	  <assets>
	    Washington.csv
	    Oregon.csv
	    California.csv
	  </assets>
	
	</exposureModel>
	
	</nrml>

As in all previous examples, the information in the metadata section is common to all of the assets in the portfolio.

The asset data can be provided in one or more csv files. The path to each of the csv files containing the asset data 
must be listed between the ``<assets>`` and ``</assets>`` xml tags.

In the example shown above, the exposure information is provided in three csv files, Washington.csv, Oregon.csv, and 
California.csv. To illustrate the format of the csv files, we have shown below the header and first few lines of the 
file Washington.csv in :ref:`the table below <exposure-csv>`.

.. _exposure-csv:
.. table:: Example exposure csv file

   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |  **id**  |   **lon**  |  **lat** | **taxonomy**  |  **number** | **structural** | **area** | **occupancy** |  **state**   |   **county**   |
   +==========+============+==========+===============+=============+================+==========+===============+==============+================+
   |    A1    |   -122.7   |   46.5   |  AGR1-W1-LC   |     7.6     |     898000     |    18    |      Agr      |  Washington  |  Lewis County  | 
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |    A2    |   -122.7   |   46.5   |  AGR1-PC1-LC  |     0.6     |     67000      |     1    |      Agr      |  Washington  |  Lewis County  |
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |    A3    |   -122.7   |   46.5   |  AGR1-C2L-PC  |     0.6     |     67000      |     1    |      Agr      |  Washington  |  Lewis County  |
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |    A4    |   -122.7   |   46.5   |  AGR1-PC1-PC  |     1.5     |     179000     |     4    |      Agr      |  Washington  |  Lewis County  |
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |    A5    |   -122.7   |   46.5   |  AGR1-S2L-LC  |     0.6     |     67000      |     1    |      Agr      |  Washington  |  Lewis County  |
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |    A6    |   -122.7   |   46.5   |  AGR1-S1L-PC  |     1.1     |     133000     |     3    |      Agr      |  Washington  |  Lewis County  |
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |    A7    |   -122.7   |   46.5   |  AGR1-S2L-PC  |     1.5     |     182000     |     4    |      Agr      |  Washington  |  Lewis County  |
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |    A8    |   -122.7   |   46.5   |  AGR1-S3-PC   |     1.1     |     130000     |     3    |      Agr      |  Washington  |  Lewis County  |
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+
   |    A9    |   -122.7   |   46.5   |  AGR1-RM1L-LC |     0.6     |     68000      |     1    |      Agr      |  Washington  |  Lewis County  |
   +----------+------------+----------+---------------+-------------+----------------+----------+---------------+--------------+----------------+

Note that the xml metadata section for exposure models provided using csv files must include the xml tag 
``<occupancyPeriods>`` listing the periods of day for which the number of occupants in each asset will be listed in the 
csv files. In case the number of occupants are not listed in the csv files, a self-closing tag ``<occupancyPeriods />`` 
should be included in the xml metadata section.

A web-based tool to build an *Exposure Model* in the Natural hazards’ Risk Markup Language schema starting from a csv 
file or a spreadsheet can be found at the OpenQuake platform at the following address: https://platform.openquake.org/ipt/.

.. [1] Within the OpenQuake engine, longitude and latitude coordinates are internally rounded to a precision of 5 digits after the decimal point.


Exposure models in XML format
-----------------------------

*************
Example XML 1
*************

This example illustrates an *Exposure Model* in which the aggregated cost (structural, nonstructural, contents and 
business interruption) of the assets of each taxonomy for a set of locations is directly provided. Thus, in order to 
indicate how the various costs will be defined, the following information needs to be stored in the *Exposure Model* file, 
as shown in the listing below:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>
	    Exposure model with aggregated replacement costs for each asset
	  </description>
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="aggregated" unit="USD" />
	      <costType name="nonstructural" type="aggregated" unit="USD" />
	      <costType name="contents" type="aggregated" unit="USD" />
	      <costType name="business_interruption" type="aggregated" unit="USD/month"/>
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" taxonomy="Adobe" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="20000" />
	        <cost type="nonstructural" value="30000" />
	        <cost type="contents" value="10000" />
	        <cost type="business_interruption" value="4000" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

In this case, the cost ``type`` of each component as been defined as ``aggregated``. Once the way in which each cost is 
going to be defined has been established, the values for each asset can be stored according to the format shown in the 
listing:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>
	    Exposure model with aggregated replacement costs for each asset
	  </description>
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="aggregated" unit="USD" />
	      <costType name="nonstructural" type="aggregated" unit="USD" />
	      <costType name="contents" type="aggregated" unit="USD" />
	      <costType name="business_interruption" type="aggregated" unit="USD/month"/>
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" taxonomy="Adobe" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="20000" />
	        <cost type="nonstructural" value="30000" />
	        <cost type="contents" value="10000" />
	        <cost type="business_interruption" value="4000" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

Each asset is uniquely identified by its ``id``. Then, a pair of coordinates (latitude and longitude) for a ``location`` 
where the asset is assumed to exist is defined. Each asset must be classified according to a ``taxonomy``, so that the 
OpenQuake engine is capable of employing the appropriate *Vulnerability Function* or *Fragility Function* in the risk 
calculations. Finally, the cost values of each ``type`` are stored within the ``costs`` attribute. In this example, the 
aggregated value for all structural units (within a given asset) at each location is provided directly, so there is no 
need to define other attributes such as ``number`` or ``area``. This mode of representing an *Exposure Model* is probably 
the simplest one.

*************
Example XML 2
*************

In the snippet shown in the listing below, an *Exposure Model* containing the number of structural units and the 
associated costs per unit of each asset is presented:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>
	    Exposure model with replacement costs per building for each asset
	  </description>
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="per_asset" unit="USD" />
	      <costType name="nonstructural" type="per_asset" unit="USD" />
	      <costType name="contents" type="per_asset" unit="USD" />
	      <costType name="business_interruption" type="per_asset" unit="USD/month"/>
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" number="2" taxonomy="Adobe" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="7500" />
	        <cost type="nonstructural" value="11250" />
	        <cost type="contents" value="3750" />
	        <cost type="business_interruption" value="1500" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

For this case, the cost ``type`` has been set to ``per_asset``. Then, the information from each asset can be stored 
following the format shown in the listing below:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>
	    Exposure model with replacement costs per building for each asset
	  </description>
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="per_asset" unit="USD" />
	      <costType name="nonstructural" type="per_asset" unit="USD" />
	      <costType name="contents" type="per_asset" unit="USD" />
	      <costType name="business_interruption" type="per_asset" unit="USD/month"/>
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" number="2" taxonomy="Adobe" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="7500" />
	        <cost type="nonstructural" value="11250" />
	        <cost type="contents" value="3750" />
	        <cost type="business_interruption" value="1500" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

In this example, the various costs for each asset is not provided directly, as in the previous example. In order to carry 
out the risk calculations in which the economic cost of each asset is provided, the OpenQuake engine multiplies, for each 
asset, the number of units (buildings) by the “per asset” replacement cost. Note that in this case, there is no need to 
specify the attribute ``area``.

*************
Example XML 3
*************

The example shown in the listing below comprises an *Exposure Model* containing the built up area of each asset, and the 
associated costs are provided per unit area:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>
	    Exposure model with replacement costs per unit area;
	    and areas provided as aggregated values for each asset
	  </description>
	  <conversions>
	    <area type="aggregated" unit="SQM" />
	    <costTypes>
	      <costType name="structural" type="per_area" unit="USD" />
	      <costType name="nonstructural" type="per_area" unit="USD" />
	      <costType name="contents" type="per_area" unit="USD" />
	      <costType name="business_interruption" type="per_area" unit="USD/month"/>
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" area="1000" taxonomy="Adobe" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="5" />
	        <cost type="nonstructural" value="7.5" />
	        <cost type="contents" value="2.5" />
	        <cost type="business_interruption" value="1" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

In order to compile an *Exposure Model* with this structure, the cost ``type`` should be set to ``per_area``. In addition, 
it is also necessary to specify if the ``area`` that is being store represents the aggregated area of number of units 
within an asset, or the average area of a single unit. In this particular case, the ``area`` that is being stored is the 
aggregated built up area per asset, and thus this attribute was set to ``aggregated``. The listing below illustrates the 
definition of the assets for this example:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>
	    Exposure model with replacement costs per unit area;
	    and areas provided as aggregated values for each asset
	  </description>
	  <conversions>
	    <area type="aggregated" unit="SQM" />
	    <costTypes>
	      <costType name="structural" type="per_area" unit="USD" />
	      <costType name="nonstructural" type="per_area" unit="USD" />
	      <costType name="contents" type="per_area" unit="USD" />
	      <costType name="business_interruption" type="per_area" unit="USD/month"/>
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" area="1000" taxonomy="Adobe" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="5" />
	        <cost type="nonstructural" value="7.5" />
	        <cost type="contents" value="2.5" />
	        <cost type="business_interruption" value="1" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

Once again, the OpenQuake engine needs to carry out some calculations in order to compute the different costs per asset. 
In this case, this value is computed by multiplying the aggregated built up ``area`` of each asset by the associated cost 
per unit area. Notice that in this case, there is no need to specify the attribute ``number``.

*************
Example XML 4
*************

This example demonstrates an *Exposure Model* that defines the number of structural units for each asset, the average 
built up area per structural unit and the associated costs per unit area. The listing below shows the metadata definition 
for an *Exposure Model* built in this manner:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>
	    Exposure model with replacement costs per unit area;
	    and areas provided per building for each asset
	  </description>
	  <conversions>
	    <area type="per_asset" unit="SQM" />
	    <costTypes>
	      <costType name="structural" type="per_area" unit="USD" />
	      <costType name="nonstructural" type="per_area" unit="USD" />
	      <costType name="contents" type="per_area" unit="USD" />
	      <costType name="business_interruption" type="per_area" unit="USD/month"/>
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" number="3" area="400" taxonomy="Adobe" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="10" />
	        <cost type="nonstructural" value="15" />
	        <cost type="contents" value="5" />
	        <cost type="business_interruption" value="2" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

Similarly to what was described in the previous example, the various costs ``type`` also need to be established as 
``per_area``, but the ``type`` of area is now defined as ``per_asset``. The listing below illustrates the definition of 
the assets for this example:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>
	    Exposure model with replacement costs per unit area;
	    and areas provided per building for each asset
	  </description>
	  <conversions>
	    <area type="per_asset" unit="SQM" />
	    <costTypes>
	      <costType name="structural" type="per_area" unit="USD" />
	      <costType name="nonstructural" type="per_area" unit="USD" />
	      <costType name="contents" type="per_area" unit="USD" />
	      <costType name="business_interruption" type="per_area" unit="USD/month"/>
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" number="3" area="400" taxonomy="Adobe" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="10" />
	        <cost type="nonstructural" value="15" />
	        <cost type="contents" value="5" />
	        <cost type="business_interruption" value="2" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

In this example, the OpenQuake engine will make use of all the parameters to estimate the various costs of each asset, by 
multiplying the number of structural units by its average built up area, and then by the respective cost per unit area.

*************
Example XML 5
*************

In this example, additional information will be included, which is required for other risk analysis besides loss 
estimation, such as the benefit/cost analysis.

In order to perform a benefit/cost assessment, it is necessary to indicate the retrofitting cost. This parameter is 
handled in the same manner as the structural cost, and it should be stored according to the format shown in the listing 
below:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>Exposure model illustrating retrofit costs</description>
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="aggregated" unit="USD"
	                retrofittedType="per_asset" retrofittedUnit="USD" />
	    </costTypes>
	  </conversions>
	  <assets>
	    <asset id="a1" taxonomy="Adobe" number="1" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="10000" retrofitted="2000" />
	      </costs>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

Despite the fact that for the demonstration of how the retrofitting cost can be stored the per building type of cost 
structure described in Example 1 was used, it is important to mention that any of the other cost storing approaches can 
also be employed (Examples 2–4).

*************
Example XML 6
*************

The example *Exposure Model* shown in the listing below illustrates how the occupants parameter is defined 
for each asset. In addition, this example also serves the purpose of presenting an *Exposure Model* in which three cost 
types have been defined using three different options.

As previously mentioned, in this example only three costs are being stored, and each one follows a different approach. 
The ``structural`` cost is being defined as the aggregate replacement cost for all of the buildings comprising the asset 
(Example 1), the ``nonstructural value`` is defined as the replacement cost per unit area where the area is defined per 
building comprising the asset (Example 4), and the ``contents`` and ``business_interruption`` values are provided per 
building comprising the asset (Example 2). The number of occupants at different times of the day are also provided as 
aggregated values for all of the buildings comprising the asset:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>Exposure model example with occupants</description>
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="aggregated" unit="USD" />
	      <costType name="nonstructural" type="per_area" unit="USD" />
	      <costType name="contents" type="per_asset" unit="USD" />
	      <costType name="business_interruption" type="per_asset" unit="USD/month" />
	    </costTypes>
	    <area type="per_asset" unit="SQM" />
	  </conversions>
	  <assets>
	    <asset id="a1" taxonomy="Adobe" number="5" area="200" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="20000" />
	        <cost type="nonstructural" value="15" />
	        <cost type="contents" value="2400" />
	        <cost type="business_interruption" value="1500" />
	      </costs>
	      <occupancies>
	        <occupancy occupants="6" period="day" />
	        <occupancy occupants="10" period="transit" />
	        <occupancy occupants="20" period="night" />
	      </occupancies>
	    </asset>
	  </assets>
	</exposureModel>
	
	</nrml>

*************
Example XML 7
*************

The example *Exposure Model* shown in the listing below illustrates how one or more tags can be defined for each asset:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example_with_tags"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>Exposure Model Example with Tags</description>
	
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="per_area" unit="USD" />
	    </costTypes>
	    <area type="per_asset" unit="SQM" />
	  </conversions>
	
	  <tagNames>state county tract city zip cresta</tagNames>
	
	  <assets>
	    <asset id="a1" taxonomy="Adobe" number="5" area="100" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="10000" />
	      </costs>
	      <occupancies>
	        <occupancy occupants="20" period="day" />
	      </occupancies>
	      <tags state="California" county="Solano" tract="252702"
	            city="Suisun" zip="94585" cresta="A.11"/>
	    </asset>
	  </assets>
	
	</exposureModel>
	
	</nrml>

The list of tag names that will be used in the *Exposure Model* must be provided in the metadata section of the exposure 
file, as shown in the following snippet from the full file:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
        xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	  <exposureModel id="exposure_example_with_tags"
	                 category="buildings"
	                 taxonomySource="GEM_Building_Taxonomy_3.3">

	    <description>Exposure Model Example with Tags</description>
	
            <conversions>

	      <costTypes>

	        <costType name="structural" type="per_area" unit="USD" />

	      </costTypes>
	      <area type="per_asset" unit="SQM" />

	    </conversions>
	
	    <tagNames>state county tract city zip cresta</tagNames>
	
	    <assets>

	      <asset id="a1" taxonomy="Adobe" number="5" area="100" >

	        <location lon="-122.000" lat="38.113" />
	        <costs>

	          <cost type="structural" value="10000"/>
	
	        </costs>
	        <occupancies>

	          <occupancy occupants="20" period="day" />
	
	        </occupancies>
	        <tags state="California" county="Solano" tract="252702" city="Suisun" zip="94585" cresta="A.11"/>

	      </asset>

	    </assets>
	
	</nrml>
	

The tag values for the different tags can then be specified for each asset as shown in the following snippet from the 
same file:

.. code-block:: xml

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<exposureModel id="exposure_example_with_tags"
	               category="buildings"
	               taxonomySource="GEM_Building_Taxonomy_3.3">
	  <description>Exposure Model Example with Tags</description>
	
	  <conversions>
	    <costTypes>
	      <costType name="structural" type="per_area" unit="USD" />
	    </costTypes>
	    <area type="per_asset" unit="SQM" />
	  </conversions>
	
	  <tagNames>state county tract city zip cresta</tagNames>
	
	  <assets>
	    <asset id="a1" taxonomy="Adobe" number="5" area="100" >
	      <location lon="-122.000" lat="38.113" />
	      <costs>
	        <cost type="structural" value="10000" />
	      </costs>
	      <occupancies>
	        <occupancy occupants="20" period="day" />
	      </occupancies>
	      <tags state="California" county="Solano" tract="252702"
	            city="Suisun" zip="94585" cresta="A.11"/>
	    </asset>
	  </assets>
	
	</exposureModel>
	
	</nrml>

Note that it is not mandatory that every tag name specified in the metadata section must be provided with a tag value 
for each asset.