Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     2,143,483,537      
date           2017-11-08T18:06:20
engine_version 2.8.0-gite3d0f56   
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
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 2           2,132        2,132       
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================== ================================================================================
count_eff_ruptures.received tot 7.39 KB, max_per_task 1.38 KB                                               
count_eff_ruptures.sent     sources 32.21 KB, param 8.77 KB, srcfilter 5.81 KB, monitor 1.92 KB, gsims 588 B
hazard.input_weight         1768.0000000000002                                                              
hazard.n_imts               1                                                                               
hazard.n_levels             19                                                                              
hazard.n_realizations       1                                                                               
hazard.n_sites              12                                                                              
hazard.n_sources            2                                                                               
hazard.output_weight        228.0                                                                           
hostname                    tstation.gem.lan                                                                
require_epsilons            True                                                                            
=========================== ================================================================================

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
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      232       AreaSource   1,612        0.016     10        124      
0      225       AreaSource   520          0.003     3         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.019     2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.005 7.005E-04 0.004 0.006 6        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.980     0.0       1     
managing sources               0.049     0.0       1     
total count_eff_ruptures       0.031     3.777     6     
prefiltering source model      0.009     0.555     1     
reading exposure               0.007     0.0       1     
store source_info              0.003     0.0       1     
aggregate curves               1.972E-04 0.0       6     
saving probability maps        2.408E-05 0.0       1     
reading site collection        6.676E-06 0.0       1     
============================== ========= ========= ======