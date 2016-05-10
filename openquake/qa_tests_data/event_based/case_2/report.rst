Event-Based Hazard QA Test, Case 2
==================================

gem-tstation:/home/michele/ssd/calc_15456.hdf5 updated Tue May 10 12:37:29 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           1.0                
ses_per_logic_tree_path      600                
truncation_level             0.0                
rupture_mesh_spacing         1.0                
complex_fault_mesh_spacing   1.0                
width_of_mfd_bin             0.001              
area_source_discretization   10.0               
random_seed                  1066               
master_seed                  0                  
oqlite_version               '0.13.0-gitcdd89a9'
============================ ===================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
trt_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           3            75    
================ ====== ==================== =========== ============ ======

Informational data
------------------
======== ==============
hostname 'gem-tstation'
======== ==============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 3    
Total number of events   3    
Rupture multiplicity     1.000
======================== =====

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  75     1         0.003       1.597E-05  2.161    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
PointSource  0.003       1.597E-05  2.161     1     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ========= ===== ===== =========
measurement                       mean  stddev    min   max   num_tasks
compute_ruptures.time_sec         2.161 NaN       2.161 2.161 1        
compute_ruptures.memory_mb        0.602 NaN       0.602 0.602 1        
compute_gmfs_and_curves.time_sec  0.002 1.276E-05 0.002 0.002 3        
compute_gmfs_and_curves.memory_mb 0.0   0.0       0.0   0.0   3        
================================= ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         2.161     0.602     1     
store source_info              0.009     0.0       1     
reading composite source model 0.007     0.0       1     
total compute_gmfs_and_curves  0.007     0.0       3     
managing sources               0.005     0.0       1     
saving ruptures                0.004     0.0       1     
filtering sources              0.003     0.0       1     
make contexts                  0.003     0.0       3     
aggregating hcurves            0.003     0.0       3     
saving gmfs                    0.002     0.0       3     
aggregate curves               0.002     0.0       4     
bulding hazard curves          8.669E-04 0.0       3     
compute poes                   8.538E-04 0.0       3     
filtering ruptures             6.282E-04 0.0       3     
reading site collection        2.599E-05 0.0       1     
splitting sources              1.597E-05 0.0       1     
============================== ========= ========= ======