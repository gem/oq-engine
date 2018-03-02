Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2018-03-01T10:45:04
engine_version 2.10.0-git18f5063  
============== ===================

num_sites = 2, num_levels = 38

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    2                
maximum_distance                {'default': 40.0}
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
=============================== =================

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
b1        0.500  trivial(1)      2/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=2)
  0,ChiouYoungs2008(): [0 1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,619        2,236       
================ ====== ==================== ============ ============

Informational data
------------------
========================== =================================================================================
count_ruptures.received    tot 3.27 KB, max_per_task 432 B                                                  
count_ruptures.sent        sources 28.46 KB, param 6.84 KB, srcfilter 6.82 KB, monitor 2.9 KB, gsims 1.12 KB
hostname                   tstation.gem.lan                                                                 
========================== =================================================================================

Slowest sources
---------------
========= ================== ============ ========= ========= =========
source_id source_class       num_ruptures calc_time num_sites num_split
========= ================== ============ ========= ========= =========
2         AreaSource         1,440        0.030     97        96       
4         ComplexFaultSource 164          0.025     11        10       
1         PointSource        15           2.627E-04 2         1        
3         SimpleFaultSource  617          0.0       1         0        
========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.030     1     
ComplexFaultSource 0.025     1     
PointSource        2.627E-04 1     
SimpleFaultSource  0.0       1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.009 0.011  0.002 0.033 9        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.272     0.0       1     
reading composite source model 0.109     0.0       1     
total count_ruptures           0.085     3.766     9     
store source_info              0.015     0.0       1     
unpickling count_ruptures      4.327E-04 0.0       9     
aggregate curves               1.938E-04 0.0       9     
reading site collection        8.965E-05 0.0       1     
saving probability maps        3.600E-05 0.0       1     
============================== ========= ========= ======