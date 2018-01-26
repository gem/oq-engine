Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     2,439,591,035      
date           2018-01-11T04:29:17
engine_version 2.9.0-git3c583c4   
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
count_ruptures.received tot 15.54 KB, max_per_task 1.55 KB                                                 
count_ruptures.sent     sources 77.88 KB, srcfilter 11.66 KB, param 6.42 KB, monitor 3.74 KB, gsims 2.05 KB
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
231       AreaSource   4,185        0.042     6         279      
376       AreaSource   2,220        1.640E-04 1         1        
288       AreaSource   2,430        0.0       1         0        
13        AreaSource   1,824        0.0       1         0        
253       AreaSource   3,058        0.0       1         0        
177       AreaSource   846          0.0       1         0        
45        AreaSource   960          0.0       1         0        
291       AreaSource   2,350        0.0       1         0        
270       AreaSource   7,837        0.0       1         0        
68        AreaSource   1,899        0.0       1         0        
325       AreaSource   3,934        0.0       1         0        
257       AreaSource   2,850        0.0       1         0        
343       AreaSource   2,926        0.0       1         0        
166       AreaSource   559          0.0       1         0        
132       AreaSource   4,131        0.0       1         0        
225       AreaSource   520          0.0       1         0        
28        AreaSource   2,548        0.0       1         0        
27        AreaSource   1,482        0.0       1         0        
198       AreaSource   760          0.0       1         0        
184       AreaSource   780          0.0       1         0        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.042     39    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.005 0.001  0.002 0.007 12       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 3.858     0.0       1     
managing sources               0.177     0.0       1     
total count_ruptures           0.065     1.344     12    
store source_info              0.006     0.0       1     
reading exposure               0.006     0.0       1     
aggregate curves               6.797E-04 0.0       12    
saving probability maps        4.435E-05 0.0       1     
reading site collection        5.484E-06 0.0       1     
============================== ========= ========= ======