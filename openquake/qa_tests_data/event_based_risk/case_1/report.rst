Event Based Risk QA Test 1
==========================

============== ===================
checksum32     261,398,150        
date           2018-02-25T06:42:45
engine_version 2.10.0-git1f7c0c0  
============== ===================

num_sites = 3, num_levels = 25

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
=========================== ====================================================================
Name                        File                                                                
=========================== ====================================================================
exposure                    `exposure.xml <exposure.xml>`_                                      
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                        
job_ini                     `job.ini <job.ini>`_                                                
nonstructural_vulnerability `vulnerability_model_nonstco.xml <vulnerability_model_nonstco.xml>`_
source                      `source_model.xml <source_model.xml>`_                              
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_        
structural_vulnerability    `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_      
=========================== ====================================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  simple(2)       2/2             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================== =========== ======================= =================
grp_id gsims                               distances   siteparams              ruptparams       
====== =================================== =========== ======================= =================
0      AkkarBommer2010() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [1]
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 18           18          
================ ====== ==================== ============ ============

Informational data
------------------
========================= ==============================================================================
compute_ruptures.received tot 16.12 KB, max_per_task 5.4 KB                                             
compute_ruptures.sent     sources 4.04 KB, param 3.04 KB, src_filter 2.43 KB, monitor 990 B, gsims 648 B
hazard.input_weight       1.8000000000000003                                                            
hazard.n_imts             5                                                                             
hazard.n_levels           25                                                                            
hazard.n_realizations     2                                                                             
hazard.n_sites            3                                                                             
hazard.n_sources          3                                                                             
hazard.output_weight      75.0                                                                          
hostname                  tstation.gem.lan                                                              
require_epsilons          True                                                                          
========================= ==============================================================================

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 2 realization(s) x 2 loss type(s) x 1 losses x 8 bytes x 20 tasks = 2.5 KB

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RM       1.000 0.0    1   1   2         2         
RC       1.000 NaN    1   1   1         1         
W        1.000 NaN    1   1   1         1         
*ALL*    1.333 0.577  1   2   3         4         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
3         PointSource  6            0.0       1         0        
1         PointSource  6            0.0       1         0        
2         PointSource  6            0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.012 0.001  0.010 0.013 3        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.035     0.0       1     
total compute_ruptures         0.035     0.0       3     
making contexts                0.012     0.0       9     
saving ruptures                0.007     0.0       3     
store source_info              0.004     0.0       1     
reading composite source model 0.003     0.0       1     
reading exposure               0.001     0.0       1     
setting event years            0.001     0.0       1     
reading site collection        5.889E-05 0.0       1     
============================== ========= ========= ======