Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     2,143,483,537      
date           2017-12-06T11:19:15
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 12, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

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
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,132        33,831      
================ ====== ==================== ============ ============

Informational data
------------------
======================= ================================================================================
count_ruptures.received tot 7.23 KB, max_per_task 1.36 KB                                               
count_ruptures.sent     sources 32.69 KB, srcfilter 5.81 KB, param 3.21 KB, monitor 1.87 KB, gsims 588 B
hazard.input_weight     3383.1000000000004                                                              
hazard.n_imts           1                                                                               
hazard.n_levels         19                                                                              
hazard.n_realizations   1                                                                               
hazard.n_sites          12                                                                              
hazard.n_sources        15                                                                              
hazard.output_weight    228.0                                                                           
hostname                tstation.gem.lan                                                                
require_epsilons        True                                                                            
======================= ================================================================================

Exposure model
--------------
=============== ========
#assets         13      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 0.0    1   1   4         4         
DS       2.000 NaN    2   2   1         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   5         5         
*ALL*    1.083 0.289  1   2   12        13        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
232       AreaSource   1,612        0.018     6         124      
225       AreaSource   520          0.003     1         1        
306       AreaSource   1,768        0.0       1         0        
101       AreaSource   559          0.0       1         0        
59        AreaSource   750          0.0       1         0        
57        AreaSource   840          0.0       1         0        
8         AreaSource   4,832        0.0       1         0        
42        AreaSource   1,755        0.0       1         0        
27        AreaSource   1,482        0.0       1         0        
125       AreaSource   8,274        0.0       1         0        
137       AreaSource   2,072        0.0       1         0        
359       AreaSource   2,314        0.0       1         0        
135       AreaSource   3,285        0.0       1         0        
253       AreaSource   3,058        0.0       1         0        
299       AreaSource   710          0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.021     15    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_ruptures     0.005 3.152E-04 0.005 0.006 6        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.921     0.0       1     
managing sources               0.058     0.0       1     
total count_ruptures           0.033     4.148     6     
reading exposure               0.007     0.0       1     
store source_info              0.003     0.0       1     
aggregate curves               1.860E-04 0.0       6     
saving probability maps        2.456E-05 0.0       1     
reading site collection        6.914E-06 0.0       1     
============================== ========= ========= ======