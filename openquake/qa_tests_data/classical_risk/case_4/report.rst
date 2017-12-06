Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     2,439,591,035      
date           2017-12-06T11:19:17
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 6, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
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
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

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
  0,AkkarBommer2010(): [0]
  0,ChiouYoungs2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 4,195        91,021      
================ ====== ==================== ============ ============

Informational data
------------------
======================= ===================================================================================
count_ruptures.received tot 16.62 KB, max_per_task 1.39 KB                                                 
count_ruptures.sent     sources 80.03 KB, srcfilter 11.27 KB, param 7.49 KB, monitor 4.36 KB, gsims 2.39 KB
hazard.input_weight     9102.1                                                                             
hazard.n_imts           1                                                                                  
hazard.n_levels         19                                                                                 
hazard.n_realizations   2                                                                                  
hazard.n_sites          6                                                                                  
hazard.n_sources        39                                                                                 
hazard.output_weight    114.0                                                                              
hostname                tstation.gem.lan                                                                   
require_epsilons        True                                                                               
======================= ===================================================================================

Exposure model
--------------
=============== ========
#assets         6       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 NaN    1   1   1         1         
W        1.000 0.0    1   1   5         5         
*ALL*    1.000 0.0    1   1   6         6         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
231       AreaSource   4,185        0.039     6         279      
376       AreaSource   2,220        1.512E-04 1         1        
257       AreaSource   2,850        0.0       1         0        
125       AreaSource   8,274        0.0       1         0        
28        AreaSource   2,548        0.0       1         0        
161       AreaSource   552          0.0       1         0        
288       AreaSource   2,430        0.0       1         0        
298       AreaSource   2,744        0.0       1         0        
270       AreaSource   7,837        0.0       1         0        
20        AreaSource   1,256        0.0       1         0        
8         AreaSource   4,832        0.0       1         0        
95        AreaSource   1,176        0.0       1         0        
198       AreaSource   760          0.0       1         0        
27        AreaSource   1,482        0.0       1         0        
395       AreaSource   2,720        0.0       1         0        
177       AreaSource   846          0.0       1         0        
137       AreaSource   2,072        0.0       1         0        
135       AreaSource   3,285        0.0       1         0        
299       AreaSource   710          0.0       1         0        
325       AreaSource   3,934        0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.039     39    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_ruptures     0.005 8.823E-04 0.003 0.007 14       
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 3.861     0.0       1     
managing sources               0.182     0.0       1     
total count_ruptures           0.063     2.012     14    
reading exposure               0.006     0.0       1     
store source_info              0.003     0.0       1     
aggregate curves               3.948E-04 0.0       14    
saving probability maps        2.503E-05 0.0       1     
reading site collection        5.960E-06 0.0       1     
============================== ========= ========= ======