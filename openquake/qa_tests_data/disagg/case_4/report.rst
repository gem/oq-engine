Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2018-03-26T15:57:46
engine_version 2.10.0-git543cfb0  
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

Slowest sources
---------------
========= ================== ============ ========= ========== ========= =========
source_id source_class       num_ruptures calc_time split_time num_sites num_split
========= ================== ============ ========= ========== ========= =========
4         ComplexFaultSource 164          0.040     2.213E-04  10        10       
2         AreaSource         1,440        0.021     0.017      96        96       
1         PointSource        15           0.001     4.768E-06  1         1        
3         SimpleFaultSource  617          0.0       1.893E-04  0         0        
========= ================== ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.021     1     
ComplexFaultSource 0.040     1     
PointSource        0.001     1     
SimpleFaultSource  0.0       1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.010 0.008  0.004 0.028 8        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ============================================================================= ========
task           sent                                                                          received
count_ruptures sources=27.43 KB param=6.08 KB srcfilter=6.06 KB monitor=2.58 KB gsims=1016 B 2.98 KB 
============== ============================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.092     0.0       1     
total count_ruptures           0.081     3.504     8     
managing sources               0.041     0.0       1     
splitting sources              0.018     0.0       1     
store source_info              0.004     0.0       1     
unpickling count_ruptures      3.080E-04 0.0       8     
reading site collection        2.801E-04 0.0       1     
aggregate curves               1.454E-04 0.0       8     
saving probability maps        2.980E-05 0.0       1     
============================== ========= ========= ======