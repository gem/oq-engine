Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     2,439,591,035      
date           2018-04-19T05:01:46
engine_version 3.1.0-git9c5da5b   
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
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
231       AreaSource   4,185        0.056     0.110      1,090     279       0     
376       AreaSource   2,220        1.504E-04 0.133      1         1         0     
161       AreaSource   552          0.0       0.047      0         0         0     
184       AreaSource   780          0.0       0.025      0         0         0     
166       AreaSource   559          0.0       0.032      0         0         0     
95        AreaSource   1,176        0.0       0.056      0         0         0     
208       AreaSource   760          0.0       0.026      0         0         0     
125       AreaSource   8,274        0.0       0.531      0         0         0     
2         AreaSource   5,446        0.0       0.175      0         0         0     
137       AreaSource   2,072        0.0       0.112      0         0         0     
89        AreaSource   810          0.0       0.081      0         0         0     
291       AreaSource   2,350        0.0       0.084      0         0         0     
369       AreaSource   826          0.0       0.025      0         0         0     
27        AreaSource   1,482        0.0       0.058      0         0         0     
288       AreaSource   2,430        0.0       0.121      0         0         0     
299       AreaSource   710          0.0       0.026      0         0         0     
257       AreaSource   2,850        0.0       0.113      0         0         0     
42        AreaSource   1,755        0.0       0.055      0         0         0     
135       AreaSource   3,285        0.0       0.187      0         0         0     
395       AreaSource   2,720        0.0       0.113      0         0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.057     39    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.010 0.005  0.003 0.020 9        
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
splitting sources              4.568     3.426     1     
reading composite source model 3.869     0.0       1     
managing sources               1.217     0.0       1     
total count_ruptures           0.093     2.355     9     
store source_info              0.023     0.0       1     
reading exposure               0.004     0.0       1     
reading site collection        0.004     0.0       1     
unpickling count_ruptures      4.280E-04 0.0       9     
aggregate curves               1.848E-04 0.0       9     
saving probability maps        3.886E-05 0.0       1     
============================== ========= ========= ======