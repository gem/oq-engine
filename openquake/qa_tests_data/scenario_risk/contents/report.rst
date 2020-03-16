Scenario QA Test for contents
=============================

============== ===================
checksum32     241_725_599        
date           2020-03-13T11:20:18
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 3, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                None              
area_source_discretization      None              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     3                 
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
====================== ======================================================================
Name                   File                                                                  
====================== ======================================================================
contents_vulnerability `vulnerability_model_contents.xml <vulnerability_model_contents.xml>`_
exposure               `exposure_model.xml <exposure_model.xml>`_                            
job_ini                `job_haz.ini <job_haz.ini>`_                                          
rupture_model          `fault_rupture.xml <fault_rupture.xml>`_                              
====================== ======================================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b_1       1.00000 1               
========= ======= ================

Exposure model
--------------
=========== =
#assets     3
#taxonomies 3
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
RM       1.00000 NaN    1   1   1         1         
RC       1.00000 NaN    1   1   1         1         
W        1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   3         3         
======== ======= ====== === === ========= ==========

Information about the tasks
---------------------------
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
================ ========= ========= ======
calc_66885       time_sec  memory_mb counts
================ ========= ========= ======
reading exposure 4.697E-04 0.0       1     
================ ========= ========= ======