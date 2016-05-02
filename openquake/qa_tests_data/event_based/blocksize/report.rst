QA test for blocksize independence (hazard)
===========================================

gem-tstation:/home/michele/ssd/calc_1027.hdf5 updated Thu Apr 28 15:43:14 2016

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 1                  
maximum_distance             {'default': 400.0} 
investigation_time           5.0                
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         10.0               
complex_fault_mesh_spacing   10.0               
width_of_mfd_bin             0.5                
area_source_discretization   10.0               
random_seed                  1024               
master_seed                  0                  
oqlite_version               '0.13.0-git93d6f64'
============================ ===================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
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
====== =============== =========== ======================= =================
trt_id gsims           distances   siteparams              ruptparams       
====== =============== =========== ======================= =================
0      ChiouYoungs2008 rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== =============== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           3            277   
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
0            1         AreaSource   175    1,170     0.002       0.611      9.402    
0            2         AreaSource   58     389       0.002       0.199      2.468    
0            3         AreaSource   44     352       0.002       0.161      1.211    
============ ========= ============ ====== ========= =========== ========== =========

Information about the tasks
---------------------------
================================= ===== ===== ===== =========
measurement                       min   max   mean  stddev   
compute_ruptures.time_sec         0.008 0.494 0.345 0.110    
compute_ruptures.memory_mb        0.0   0.0   0.0   0.0      
compute_gmfs_and_curves.time_sec  0.002 0.002 0.002 1.870E-05
compute_gmfs_and_curves.memory_mb 0.0   0.0   0.0   0.0      
================================= ===== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         13        0.0       38    
reading composite source model 3.460     0.0       1     
managing sources               1.249     0.0       1     
splitting sources              0.971     0.0       3     
store source_info              0.061     0.0       1     
filtering sources              0.014     0.0       9     
total compute_gmfs_and_curves  0.006     0.0       3     
saving ruptures                0.004     0.0       1     
make contexts                  0.003     0.0       3     
aggregate curves               0.002     0.0       38    
compute poes                   0.002     0.0       3     
saving gmfs                    0.002     0.0       3     
filtering ruptures             0.001     0.0       3     
reading site collection        5.102E-05 0.0       1     
============================== ========= ========= ======