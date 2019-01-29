QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     1,811,660,702      
date           2019-01-27T08:28:40
engine_version 3.4.0-git7f110aaa0b
============== ===================

num_sites = 2, num_levels = 38

Parameters
----------
=============================== ==================
calculation_mode                'disaggregation'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
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
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=1)
  0,ChiouYoungs2008(): [0]
  1,ChiouYoungs2008(): [0]
  2,ChiouYoungs2008(): [0]
  3,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 15           15          
source_model.xml 1      Active Shallow Crust 1,440        1,440       
source_model.xml 2      Active Shallow Crust 617          617         
source_model.xml 3      Active Shallow Crust 164          164         
================ ====== ==================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 2,236
#tot_ruptures 2,236
#tot_weight   1,418
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
1      2         A    1     5     1,440        1.86479   1.24299    96        96        144    
2      3         S    5     7     617          0.97720   0.00109    10        10        617    
3      4         C    7     11    164          0.37129   2.09546    10        10        656    
0      1         P    0     1     15           0.02143   1.812E-05  1.00000   1         1.50000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.86479   1     
C    0.37129   1     
P    0.02143   1     
S    0.97720   1     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.04164 NaN       0.04164 0.04164 1      
split_filter       0.24827 NaN       0.24827 0.24827 1      
classical          0.64833 0.84671   0.14369 2.14523 5      
build_hazard_stats 0.00614 9.628E-04 0.00546 0.00682 2      
================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=4, weight=152, duration=0 s, sources="4"

======== ======= ====== ======= === =
variable mean    stddev min     max n
======== ======= ====== ======= === =
nsites   1.00000 0.0    1       1   4
weight   38      26     4.00000 64  4
======== ======= ====== ======= === =

Slowest task
------------
taskno=0, weight=321, duration=2 s, sources="4"

======== ======= ====== ======= === ==
variable mean    stddev min     max n 
======== ======= ====== ======= === ==
nsites   1.00000 0.0    1       1   99
weight   3.24747 12     1.50000 88  99
======== ======= ====== ======= === ==

Data transfer
-------------
================== =========================================================== =========
task               sent                                                        received 
read_source_models converter=313 B fnames=103 B                                4.05 KB  
split_filter       srcs=3.4 KB srcfilter=253 B seed=14 B                       101.78 KB
classical          group=99.11 KB src_filter=4.39 KB param=4.02 KB gsims=635 B 5.67 KB  
build_hazard_stats pgetter=5.73 KB hstats=134 B individual_curves=26 B         684 B    
================== =========================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          3.24167   0.90234   5     
make_contexts            1.63715   0.0       2,236 
get_poes                 0.92530   0.0       2,236 
total split_filter       0.24827   1.91016   1     
total read_source_models 0.04164   0.94531   1     
total build_hazard_stats 0.01229   1.34375   2     
combine pmaps            0.01113   1.34375   2     
managing sources         0.00705   0.00781   1     
saving probability maps  0.00530   0.0       1     
store source model       0.00511   0.0       1     
store source_info        0.00221   0.0       1     
aggregate curves         0.00187   0.0       5     
saving statistics        9.170E-04 0.0       2     
compute mean             4.776E-04 0.0       1     
======================== ========= ========= ======