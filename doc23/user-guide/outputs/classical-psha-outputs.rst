Outputs from Classical PSHA
===========================

By default, the classical PSHA calculator computes and stores hazard curves for each logic tree sample considered.

When the PSHA input model doesn’t contain epistemic uncertainties the results is a set of hazard curves (one for each 
investigated site). The command below illustrates how it is possible to retrieve the group of hazard curves obtained for 
a calculation with a given identifier ``<calc_id>`` (see Section :ref:`Exporting results from a hazard calculation <export-hazard-results>`
for an explanation about how to obtain the list of calculations performed with their corresponding ID)::
	
	user@ubuntu:~$ oq engine --lo <calc_id>
	id | name
	3  | Hazard Curves
	4  | Realizations

To export from the database the outputs (in this case hazard curves) contained in one of the output identifies, one can 
do so with the following command::

	user@ubuntu:~$ oq engine --export-output <output_id> <output_directory>

Alternatively, if the user wishes to export all of the outputs associated with a particular calculation then they can 
use the ``--export-outputs`` with the corresponding calculation key::

	user@ubuntu:~$ oq engine --export-outputs <calc_id> <output_directory>

The exports will produce one or more CSV files containing the seismic
hazard curves as represented in the listing
<lst:output_hazard_curves_csv>` below.

.. container:: listing

   .. code:: csv
      :number-lines:
      :name: lst:output_hazard_curves_csv

      #,,,,,"generated_by='OpenQuake engine 3.18.0', start_date='2023-10-03T06:09:08', checksum=2107362341, kind='mean', investigation_time=1.0, imt='PGA'"
      lon,lat,depth,poe-0.1000000,poe-0.4000000,poe-0.6000000
      0.00000,0.00000,-0.10000,4.553860E-01,5.754042E-02,6.354511E-03
      0.10000,0.00000,-0.10000,1.522632E-01,0.000000E+00,0.000000E+00
      0.20000,0.00000,-0.10000,3.037810E-03,0.000000E+00,0.000000E+00
      0.30000,0.00000,-0.10000,0.000000E+00,0.000000E+00,0.000000E+00

Notwithstanding the intuitiveness of this file, let’s have a brief overview of the information included. The overall 
content of this file is a list of hazard curves, one for each investigated site, computed using a PSHA input model 
representing one possible realisation obtained using the complete logic tree structure.

The first commented line contains some metadata like the version of the
engine used to generate the file, the start date of the calculation, a
checksum, the kind of hazard curves generated (in the example they are
mean curves), the investigation time and the IMT used (in the example PGA).

The header line indicates the contents of each column, beginning with the 
site coordinates (*lon, lat,* and *depth*) and then one column corresponding
to each intensity measure level (IML) specified in the job file for the
given IMT. These columns are named using the format *poe-<IML>* to be
interpretted as ``the probability that the IMT will exceed the given IML
during the investigation time.`` Each row then gives - for one site - the
probabilities of exceedance associated with each of the IMLs.

If the hazard calculation is configured to produce results including seismic hazard maps and uniform hazard spectra, 
then the list of outputs would display the following::

	user@ubuntu:~$ oq engine --lo <calc_id>
	id | name
	2 | Full Report
	3 | Hazard Curves
	4 | Hazard Maps
	5 | Realizations
	6 | Uniform Hazard Spectra

:ref:`The first listing <lst:output_hazard_map_csv>` below
shows a sample of the CSV file used to describe a hazard map, and and
:ref:`the second listing <lst:output_uhs>` below shows a sample of the
CSV used to describe a uniform hazard spectrum.
In both cases, the files contain a commented line as in the 	
:ref:`hazard curve lst:output_hazard_curves_csv`. The following	
row has the column headers: the site coordinates (*lon, lat*), and then a 	
set of two-part column names that indicate the IMT and probability	
of exceedance corresponding to the investigation time; the remaining rows	
give the values for each site. 
.. container:: listing

   .. code:: xml
      :number-lines:
      :name: lst:output_hazard_map_csv

      #,,,,"generated_by='OpenQuake engine 3.18.0', start_date='2023-10-03T06:09:09', checksum=969346546, kind='mean', investigation_time=1.0"
      lon,lat,PGA-0.002105,SA(0.2)-0.002105,SA(1.0)-0.002105
      -123.23738,49.27479,3.023730E-03,1.227876E-02,1.304533E-02
      -123.23282,49.26162,2.969411E-03,1.210481E-02,1.294509E-02
      -123.20480,49.26786,2.971350E-03,1.211078E-02,1.294870E-02

.. container:: listing

   .. code:: xml
      :number-lines:
      :name: lst:output_uhs

      #,,,,"generated_by='OpenQuake engine 3.15.0', start_date='2022-05-14T10:44:47', checksum=2967670219, kind='rlz-001', investigation_time=1.0"
      lon,lat,0.002105~PGA,0.002105~SA(0.2),0.002105~SA(1.0)
      -123.23738,49.27479,2.651139E-03,1.120929E-02,1.218275E-02
      -123.23282,49.26162,2.603451E-03,1.105909E-02,1.208975E-02
      -123.20480,49.26786,2.605109E-03,1.106432E-02,1.209299E-02
