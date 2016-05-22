QA test for blocksize independence (hazard)
===========================================

gem-tstation:/home/michele/ssd/calc_16412.hdf5 updated Wed May 18 18:20:16 2016

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
oqlite_version               '0.13.0-git034c0a0'
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
====== ================= =========== ======================= =================
trt_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1,b1,w=1.0>']>

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
0            1         AreaSource   175    1,170     7.050E-04   0.290      2.499    
0            2         AreaSource   58     389       8.960E-04   0.083      0.722    
0            3         AreaSource   44     352       6.781E-04   0.069      0.314    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.002       0.441      3.536     3     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.178 0.057  0.047 0.261 20       
compute_ruptures.memory_mb        0.0   0.0    0.0   0.0   20       
compute_gmfs_and_curves.time_sec  0.003 0.001  0.002 0.004 3        
compute_gmfs_and_curves.memory_mb 0.0   0.0    0.0   0.0   3        
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         3.556     0.0       20    
reading composite source model 1.606     0.0       1     
managing sources               0.540     0.0       1     
splitting sources              0.441     0.0       3     
store source_info              0.019     0.0       1     
total compute_gmfs_and_curves  0.009     0.0       3     
filtering sources              0.006     0.0       9     
aggregate curves               0.005     0.0       20    
compute poes                   0.005     0.0       3     
saving ruptures                0.004     0.0       1     
saving gmfs                    0.003     0.0       3     
make contexts                  0.003     0.0       3     
filtering ruptures             7.970E-04 0.0       3     
reading site collection        4.101E-05 0.0       1     
============================== ========= ========= ======