Scenario QA Test for contents
=============================

============== ====================
checksum32     612_967_961         
date           2020-11-02T09:35:34 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 3, num_levels = 3, num_rlzs = ?

Parameters
----------
=============================== ======================================
calculation_mode                'scenario'                            
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 300), (10.0, 300)]}
investigation_time              None                                  
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            10.0                                  
complex_fault_mesh_spacing      10.0                                  
width_of_mfd_bin                None                                  
area_source_discretization      None                                  
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     3                                     
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

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

Exposure model
--------------
=========== =
#assets     3
#taxonomies 3
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
RM       1          1.00000 nan    1   1   1        
RC       1          1.00000 nan    1   1   1        
W        1          1.00000 nan    1   1   1        
*ALL*    3          1.00000 0%     1   1   3        
======== ========== ======= ====== === === =========

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
calc_47235       time_sec  memory_mb counts
================ ========= ========= ======
importing inputs 0.02097   0.0       1     
reading exposure 4.618E-04 0.0       1     
================ ========= ========= ======