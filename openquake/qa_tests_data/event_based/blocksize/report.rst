QA test for blocksize independence (hazard)
===========================================

gem-tstation:/home/michele/ssd/calc_22617.hdf5 updated Tue May 31 15:38:51 2016

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ===============================
calculation_mode             'event_based'                  
number_of_logic_tree_samples 1                              
maximum_distance             {'Active Shallow Crust': 400.0}
investigation_time           5.0                            
ses_per_logic_tree_path      1                              
truncation_level             3.0                            
rupture_mesh_spacing         10.0                           
complex_fault_mesh_spacing   10.0                           
width_of_mfd_bin             0.5                            
area_source_discretization   10.0                           
random_seed                  1024                           
master_seed                  0                              
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

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
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           3            277   
================ ====== ==================== =========== ============ ======

Informational data
------------------
======== ============
hostname gem-tstation
======== ============

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
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   175    1,170     7.520E-04   0.279      2.309    
0            2         AreaSource   58     389       7.472E-04   0.090      0.698    
0            3         AreaSource   44     352       7.701E-04   0.074      0.298    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.002       0.443      3.305     3     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ========= ===== ===== =========
measurement                       mean  stddev    min   max   num_tasks
compute_ruptures.time_sec         0.166 0.053     0.046 0.253 20       
compute_ruptures.memory_mb        0.0   0.0       0.0   0.0   20       
compute_gmfs_and_curves.time_sec  0.002 2.680E-05 0.002 0.002 3        
compute_gmfs_and_curves.memory_mb 0.0   0.0       0.0   0.0   3        
================================= ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         3.325     0.0       20    
reading composite source model 1.614     0.0       1     
managing sources               0.619     0.0       1     
splitting sources              0.443     0.0       3     
store source_info              0.014     0.0       1     
filtering sources              0.007     0.0       9     
total compute_gmfs_and_curves  0.007     0.0       3     
compute poes                   0.004     0.0       3     
aggregate curves               0.003     0.0       20    
saving ruptures                0.003     0.0       1     
make contexts                  0.002     0.0       3     
saving gmfs                    0.002     0.0       3     
filtering ruptures             7.961E-04 0.0       3     
reading site collection        3.886E-05 0.0       1     
============================== ========= ========= ======