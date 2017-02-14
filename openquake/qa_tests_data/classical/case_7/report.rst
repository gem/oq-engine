Classical Hazard QA Test, Case 7
================================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85569.hdf5 Tue Feb 14 15:45:35 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

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
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
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
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
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
source_model_1.xml 0      Active Shallow Crust 2           1386         1,386       
source_model_2.xml 1      Active Shallow Crust 1           901          901         
================== ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      3    
#eff_ruptures 2,287
#tot_ruptures 2,287
#tot_weight   3,742
============= =====

Informational data
------------------
=========================================== ============
count_eff_ruptures_max_received_per_task    1,281       
count_eff_ruptures_num_tasks                5           
count_eff_ruptures_sent.gsims               455         
count_eff_ruptures_sent.monitor             5,275       
count_eff_ruptures_sent.sources             5,659       
count_eff_ruptures_sent.srcfilter           3,550       
count_eff_ruptures_tot_received             6,402       
hazard.input_weight                         3,742       
hazard.n_imts                               1           
hazard.n_levels                             3           
hazard.n_realizations                       2           
hazard.n_sites                              1           
hazard.n_sources                            3           
hazard.output_weight                        6.000       
hostname                                    gem-tstation
require_epsilons                            False       
=========================================== ============

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      2         ComplexFaultSource 485          0.0       1         0        
0      1         SimpleFaultSource  901          0.0       1         0        
1      1         SimpleFaultSource  901          0.0       1         0        
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
================== ==== ====== === === =========
operation-duration mean stddev min max num_tasks
count_eff_ruptures 122  31     73  146 5        
================== ==== ====== === === =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         610       24        5     
reading composite source model   6.536     0.0       1     
managing sources                 0.009     0.0       1     
filtering composite source model 0.003     0.0       1     
store source_info                0.001     0.0       1     
aggregate curves                 1.495E-04 0.0       5     
saving probability maps          4.768E-05 0.0       1     
reading site collection          4.458E-05 0.0       1     
================================ ========= ========= ======