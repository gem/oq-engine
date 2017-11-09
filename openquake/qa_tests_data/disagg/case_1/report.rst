QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     629,585,928        
date           2017-11-08T18:08:05
engine_version 2.8.0-gite3d0f56   
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
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     9000              
master_seed                     0                 
=============================== ==================

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
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=1)
  0,ChiouYoungs2008(): [0]
  1,ChiouYoungs2008(): [0]
  2,ChiouYoungs2008(): [0]
  3,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           15           15          
source_model.xml 1      Active Shallow Crust 1           1,440        1,440       
source_model.xml 2      Active Shallow Crust 1           617          617         
source_model.xml 3      Active Shallow Crust 1           164          164         
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   4    
#sources      4    
#eff_ruptures 2,236
#tot_ruptures 2,236
#tot_weight   0    
============= =====

Informational data
------------------
=========================== ===============================================================================
count_eff_ruptures.received tot 4.07 KB, max_per_task 764 B                                                
count_eff_ruptures.sent     sources 9.46 KB, param 7.19 KB, srcfilter 4.17 KB, monitor 1.92 KB, gsims 588 B
hazard.input_weight         1418.5                                                                         
hazard.n_imts               2                                                                              
hazard.n_levels             38                                                                             
hazard.n_realizations       1                                                                              
hazard.n_sites              2                                                                              
hazard.n_sources            4                                                                              
hazard.output_weight        76.0                                                                           
hostname                    tstation.gem.lan                                                               
require_epsilons            False                                                                          
=========================== ===============================================================================

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
2      3         SimpleFaultSource  617          0.029     1         10       
3      4         ComplexFaultSource 164          0.025     1         10       
1      2         AreaSource         1,440        0.001     1         1        
0      1         PointSource        15           2.062E-04 1         1        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.001     1     
ComplexFaultSource 0.025     1     
PointSource        2.062E-04 1     
SimpleFaultSource  0.029     1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ========= ===== =========
operation-duration mean  stddev min       max   num_tasks
count_eff_ruptures 0.010 0.007  9.778E-04 0.018 6        
================== ===== ====== ========= ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.148     0.0       1     
total count_eff_ruptures       0.060     0.0       6     
reading composite source model 0.029     0.0       1     
prefiltering source model      0.003     0.0       1     
store source_info              0.003     0.0       1     
aggregate curves               1.175E-04 0.0       6     
reading site collection        3.195E-05 0.0       1     
saving probability maps        2.408E-05 0.0       1     
============================== ========= ========= ======