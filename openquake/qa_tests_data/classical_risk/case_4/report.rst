Classical Hazard-Risk QA test 4
===============================

============== ===================
checksum32     3,002,809,595      
date           2019-01-20T07:36:27
engine_version 3.4.0-git452d0c6835
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
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2/2             
========= ======= =============== ================

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
source_model.xml 0      Active Shallow Crust 4,545        91,021      
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         6       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
W        1.00000 0.0    1   1   5         5         
A        1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   6         6         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      10        A    0     4     1,920        0.0       0.0        0.0       0         0.0   
0      101       A    4     10    559          0.0       0.0        0.0       0         0.0   
0      125       A    10    14    8,274        0.0       0.0        0.0       0         0.0   
0      127       A    14    20    2,940        0.0       0.0        0.0       0         0.0   
0      13        A    20    24    1,824        0.0       0.0        0.0       0         0.0   
0      132       A    24    28    4,131        0.0       0.0        0.0       0         0.0   
0      135       A    28    32    3,285        0.0       0.0        0.0       0         0.0   
0      137       A    32    36    2,072        0.0       0.0        0.0       0         0.0   
0      161       A    36    40    552          0.0       0.0        0.0       0         0.0   
0      166       A    40    44    559          0.0       0.0        0.0       0         0.0   
0      177       A    44    48    846          0.0       0.0        0.0       0         0.0   
0      184       A    48    52    780          0.0       0.0        0.0       0         0.0   
0      198       A    52    56    760          0.0       0.0        0.0       0         0.0   
0      2         A    56    60    5,446        0.0       0.0        0.0       0         0.0   
0      20        A    60    64    1,256        0.0       0.0        0.0       0         0.0   
0      208       A    64    70    760          0.0       0.0        0.0       0         0.0   
0      225       A    70    73    520          0.0       0.0        0.0       0         0.0   
0      231       A    73    77    4,185        0.0       25         0.0       279       0.0   
0      253       A    77    83    3,058        0.0       0.0        0.0       0         0.0   
0      257       A    83    87    2,850        0.0       0.0        0.0       0         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       39    
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 2.94014 NaN     2.94014 2.94014 1      
split_filter       0.37340 0.05466 0.33475 0.41205 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ========================================= ========
task               sent                                      received
read_source_models converter=388 B fnames=111 B              33.03 KB
split_filter       srcs=46.1 KB srcfilter=3.21 KB seed=182 B 74.6 KB 
================== ========================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 2.94014   1.14062   1     
total split_filter       0.74679   2.09766   2     
reading exposure         4.296E-04 0.0       1     
======================== ========= ========= ======