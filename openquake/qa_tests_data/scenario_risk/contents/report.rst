Scenario QA Test for contents
=============================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_67012.hdf5 Wed Nov  9 08:16:40 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ =================
calculation_mode             'scenario'       
number_of_logic_tree_samples 0                
maximum_distance             {u'default': 300}
investigation_time           None             
ses_per_logic_tree_path      1                
truncation_level             3.0              
rupture_mesh_spacing         10.0             
complex_fault_mesh_spacing   10.0             
width_of_mfd_bin             None             
area_source_discretization   None             
random_seed                  3                
master_seed                  0                
============================ =================

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

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b_1~b1,w=1.0>']>

Exposure model
--------------
=============== ========
#assets         3       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RC       1.000 NaN    1   1   1         1         
RM       1.000 NaN    1   1   1         1         
W        1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   3         3         
======== ===== ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.005     0.0       1     
reading exposure        0.003     0.0       1     
reading site collection 9.060E-06 0.0       1     
======================= ========= ========= ======