Event-Based Hazard QA Test, Case 18
===================================

Datastore /home/michele/ssd/calc_10568.hdf5 last updated Tue Apr 19 05:58:49 2016 on gem-tstation

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 3                  
maximum_distance             {'default': 200.0} 
investigation_time           1.0                
ses_per_logic_tree_path      350                
truncation_level             0.0                
rupture_mesh_spacing         1.0                
complex_fault_mesh_spacing   1.0                
width_of_mfd_bin             0.001              
area_source_discretization   10.0               
random_seed                  1064               
master_seed                  0                  
oqlite_version               '0.13.0-git7c9cf8e'
============================ ===================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `three_gsim_logic_tree.xml <three_gsim_logic_tree.xml>`_    
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        0.333  `source_model.xml <source_model.xml>`_ simple(3)       3/3             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================== ========= ========== ==========
trt_id gsims                              distances siteparams ruptparams
====== ================================== ========= ========== ==========
0      AkkarBommer2010 CauzziFaccioli2008 rhypo rjb vs30       rake mag  
====== ================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=3)
  0,AkkarBommer2010: ['<0,b1,AB,w=0.333333333333>', '<1,b1,AB,w=0.333333333333>']
  0,CauzziFaccioli2008: ['<2,b1,CF,w=0.333333333333>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           6            75    
================ ====== ==================== =========== ============ ======

Informational data
------------------
======== ==============
hostname 'gem-tstation'
======== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  75     1         0.004       1.693E-05  3.042    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         3.043     0.0       1     
total compute_gmfs_and_curves  0.011     0.0       6     
store source_info              0.010     0.0       1     
saving gmfs                    0.008     0.0       6     
reading composite source model 0.008     0.0       1     
managing sources               0.006     0.0       1     
saving ruptures                0.005     0.0       1     
make contexts                  0.005     0.0       6     
filtering sources              0.004     0.0       1     
compute poes                   0.003     0.0       6     
filtering ruptures             0.001     0.0       6     
aggregate curves               0.001     0.0       1     
reading site collection        3.004E-05 0.0       1     
splitting sources              1.693E-05 0.0       1     
============================== ========= ========= ======