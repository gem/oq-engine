Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     2,439,591,035      
date           2018-03-26T15:54:38
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 6, num_levels = 19

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
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
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
W        1.000 0.0    1   1   5         5         
A        1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   6         6         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========== ========= =========
source_id source_class num_ruptures calc_time split_time num_sites num_split
========= ============ ============ ========= ========== ========= =========
231       AreaSource   4,185        0.056     0.056      1,090     279      
376       AreaSource   2,220        1.087E-04 0.040      1         1        
95        AreaSource   1,176        0.0       0.031      0         0        
325       AreaSource   3,934        0.0       0.051      0         0        
42        AreaSource   1,755        0.0       0.029      0         0        
166       AreaSource   559          0.0       0.016      0         0        
132       AreaSource   4,131        0.0       0.097      0         0        
90        AreaSource   285          0.0       0.027      0         0        
161       AreaSource   552          0.0       0.024      0         0        
135       AreaSource   3,285        0.0       0.103      0         0        
28        AreaSource   2,548        0.0       0.040      0         0        
257       AreaSource   2,850        0.0       0.061      0         0        
125       AreaSource   8,274        0.0       0.211      0         0        
270       AreaSource   7,837        0.0       0.133      0         0        
127       AreaSource   2,940        0.0       0.112      0         0        
8         AreaSource   4,832        0.0       0.272      0         0        
198       AreaSource   760          0.0       0.030      0         0        
253       AreaSource   3,058        0.0       0.060      0         0        
225       AreaSource   520          0.0       0.009      0         0        
89        AreaSource   810          0.0       0.035      0         0        
========= ============ ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.056     39    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.010 0.004  0.003 0.016 9        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ============================================================================ ========
task           sent                                                                         received
count_ruptures sources=69.43 KB srcfilter=8.75 KB param=4.82 KB monitor=2.9 KB gsims=1.9 KB 3.22 KB 
============== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 4.549     0.0       1     
splitting sources              2.234     3.672     1     
managing sources               0.671     0.0       1     
total count_ruptures           0.088     1.711     9     
reading exposure               0.006     0.0       1     
store source_info              0.004     0.0       1     
unpickling count_ruptures      3.211E-04 0.0       9     
aggregate curves               1.199E-04 0.0       9     
reading site collection        4.292E-05 0.0       1     
saving probability maps        2.384E-05 0.0       1     
============================== ========= ========= ======