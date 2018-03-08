QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     165,656,583        
date           2018-03-01T10:45:06
engine_version 2.10.0-git18f5063  
============== ===================

num_sites = 2, num_levels = 38

Parameters
----------
=============================== ==================
calculation_mode                'disaggregation'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     9000              
master_seed                     0                 
ses_seed                        42                
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
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,455        15          
source_model.xml 1      Active Shallow Crust 1,455        1,440       
source_model.xml 2      Active Shallow Crust 617          617         
source_model.xml 3      Active Shallow Crust 164          164         
================ ====== ==================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 3,691
#tot_ruptures 2,236
#tot_weight   1,418
============= =====

Informational data
------------------
========================== ===============================================================================
count_ruptures.received    tot 1.86 KB, max_per_task 443 B                                                
count_ruptures.sent        sources 26.38 KB, param 3.8 KB, srcfilter 3.79 KB, monitor 1.61 KB, gsims 635 B
hostname                   tstation.gem.lan                                                               
========================== ===============================================================================

Slowest sources
---------------
========= ================== ============ ========= ========= =========
source_id source_class       num_ruptures calc_time num_sites num_split
========= ================== ============ ========= ========= =========
2         AreaSource         1,440        0.053     193       192      
3         SimpleFaultSource  617          0.023     11        10       
4         ComplexFaultSource 164          0.020     11        10       
1         PointSource        15           3.834E-04 3         2        
========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.053     1     
ComplexFaultSource 0.020     1     
PointSource        3.834E-04 1     
SimpleFaultSource  0.023     1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.021 0.022  0.009 0.059 5        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.336     0.0       1     
reading composite source model 0.154     0.0       1     
total count_ruptures           0.105     0.211     5     
store source_info              0.005     0.0       1     
unpickling count_ruptures      2.496E-04 0.0       5     
aggregate curves               1.349E-04 0.0       5     
reading site collection        7.987E-05 0.0       1     
saving probability maps        3.576E-05 0.0       1     
============================== ========= ========= ======