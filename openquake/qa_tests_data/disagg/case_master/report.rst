disaggregation with a complex logic tree
========================================

============== ===================
checksum32     2,651,285,143      
date           2017-11-11T09:42:24
engine_version 2.8.0-git5be58aa   
============== ===================

num_sites = 2, num_imts = 2

Parameters
----------
=============================== ==================
calculation_mode                'disaggregation'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     24                
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
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        0.250  complex(2,2)    4/4             
b2        0.750  complex(2,2)    4/4             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): [0 1]
  0,ChiouYoungs2008(): [2 3]
  1,AkkarBommer2010(): [0 2]
  1,ChiouYoungs2008(): [1 3]
  2,BooreAtkinson2008(): [4 5]
  2,ChiouYoungs2008(): [6 7]
  3,AkkarBommer2010(): [4 6]
  3,ChiouYoungs2008(): [5 7]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ============
source_model       grp_id trt                  num_sources eff_ruptures tot_ruptures
================== ====== ==================== =========== ============ ============
source_model_1.xml 0      Active Shallow Crust 1           543          543         
source_model_1.xml 1      Stable Shallow Crust 1           4            4           
source_model_2.xml 2      Active Shallow Crust 1           543          543         
source_model_2.xml 3      Stable Shallow Crust 1           1            1           
================== ====== ==================== =========== ============ ============

============= =====
#TRT models   4    
#sources      4    
#eff_ruptures 1,091
#tot_ruptures 1,091
#tot_weight   0    
============= =====

Informational data
------------------
=========================== ====================================================================================
count_eff_ruptures.received tot 10.14 KB, max_per_task 742 B                                                    
count_eff_ruptures.sent     sources 29.06 KB, param 17.06 KB, srcfilter 11.12 KB, monitor 5.12 KB, gsims 2.79 KB
hazard.input_weight         2182.0                                                                              
hazard.n_imts               2                                                                                   
hazard.n_levels             22                                                                                  
hazard.n_realizations       8                                                                                   
hazard.n_sites              2                                                                                   
hazard.n_sources            4                                                                                   
hazard.output_weight        44.0                                                                                
hostname                    tstation.gem.lan                                                                    
require_epsilons            False                                                                               
=========================== ====================================================================================

Slowest sources
---------------
====== ========= ========================= ============ ========= ========= =========
grp_id source_id source_class              num_ruptures calc_time num_sites num_split
====== ========= ========================= ============ ========= ========= =========
2      1         SimpleFaultSource         543          0.045     2         15       
0      1         SimpleFaultSource         543          0.044     2         15       
1      2         SimpleFaultSource         4            0.005     2         1        
3      2         CharacteristicFaultSource 1            0.002     2         1        
====== ========= ========================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
========================= ========= ======
source_class              calc_time counts
========================= ========= ======
CharacteristicFaultSource 0.002     1     
SimpleFaultSource         0.094     3     
========================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.007 0.004  0.002 0.017 16       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.188     0.0       1     
total count_eff_ruptures       0.113     4.043     16    
reading composite source model 0.036     0.0       1     
prefiltering source model      0.011     0.773     1     
store source_info              0.005     0.0       1     
aggregate curves               3.476E-04 0.0       16    
reading site collection        4.554E-05 0.0       1     
saving probability maps        3.386E-05 0.0       1     
============================== ========= ========= ======