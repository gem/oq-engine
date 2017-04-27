Classical Hazard QA Test, Case 7
================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7611.hdf5 Wed Apr 26 15:55:37 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1066              
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.700  `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/1             
b2        0.300  `source_model_2.xml <source_model_2.xml>`_ trivial(1)      1/1             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
1      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): ['<0,b1~b1,w=0.699999988079071>']
  1,SadighEtAl1997(): ['<1,b2~b1,w=0.30000001192092896>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust 2           140          140         
source_model_2.xml 1      Active Shallow Crust 1           91           91          
================== ====== ==================== =========== ============ ============

============= ===
#TRT models   2  
#sources      3  
#eff_ruptures 231
#tot_ruptures 231
#tot_weight   378
============= ===

Informational data
------------------
============================== ==========================================================================
count_eff_ruptures.received    tot 3.14 KB, max_per_task 1.05 KB                                         
count_eff_ruptures.sent        sources 4.57 KB, monitor 2.49 KB, srcfilter 2 KB, gsims 273 B, param 195 B
hazard.input_weight            378                                                                       
hazard.n_imts                  1 B                                                                       
hazard.n_levels                3 B                                                                       
hazard.n_realizations          2 B                                                                       
hazard.n_sites                 1 B                                                                       
hazard.n_sources               3 B                                                                       
hazard.output_weight           6.000                                                                     
hostname                       tstation.gem.lan                                                          
require_epsilons               0 B                                                                       
============================== ==========================================================================

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
1      1         SimpleFaultSource  91           0.0       1         0        
0      1         SimpleFaultSource  91           0.0       1         0        
0      2         ComplexFaultSource 49           0.0       1         0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.0       1     
SimpleFaultSource  0.0       2     
================== ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.227 0.269  0.069 0.538 3        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         0.681     0.0       3     
reading composite source model   0.119     0.0       1     
filtering composite source model 0.004     0.0       1     
store source_info                0.001     0.0       1     
managing sources                 1.154E-04 0.0       1     
aggregate curves                 7.415E-05 0.0       3     
reading site collection          5.460E-05 0.0       1     
saving probability maps          5.364E-05 0.0       1     
================================ ========= ========= ======