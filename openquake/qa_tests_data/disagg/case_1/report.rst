QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     1,811,660,702      
date           2019-03-14T01:45:17
engine_version 3.4.0-gita06742ffe6
============== ===================

num_sites = 2, num_levels = 38, num_rlzs = 1

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
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=1)
  0,'[ChiouYoungs2008]': [0]
  1,'[ChiouYoungs2008]': [0]
  2,'[ChiouYoungs2008]': [0]
  3,'[ChiouYoungs2008]': [0]>

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
1      2         A    1     5     1,440        2.62153   1.20797    96        96        144    
2      3         S    5     7     617          1.28188   0.00117    10        10        617    
3      4         C    7     11    164          0.56362   2.02587    10        10        656    
0      1         P    0     1     15           0.02999   1.764E-05  1.00000   1         1.50000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.62153   1     
C    0.56362   1     
P    0.02999   1     
S    1.28188   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.03063 NaN       0.03063 0.03063 1      
split_filter       0.24024 NaN       0.24024 0.24024 1      
classical          0.90306 1.16419   0.22775 2.96671 5      
build_hazard_stats 0.00590 8.289E-04 0.00531 0.00649 2      
================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=3, weight=328, duration=0 s, sources="3 4"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   1.00000 0.0     1   1   4
weight   82      5.16398 76  88  4
======== ======= ======= === === =

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
split_filter       srcs=3.4 KB srcfilter=253 B dummy=14 B                      101.78 KB
classical          group=99.11 KB param=4.02 KB src_filter=1.07 KB gsims=775 B 703.98 KB
build_hazard_stats pgetter=5.67 KB hstats=130 B N=28 B individual_curves=26 B  684 B    
================== =========================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          4.51530   2.21875   5     
make_contexts            1.63438   0.0       2,236 
get_poes                 0.94051   0.0       2,236 
total split_filter       0.24024   2.75000   1     
total read_source_models 0.03063   0.65625   1     
aggregate curves         0.02417   1.40625   5     
saving probability maps  0.01816   0.0       1     
total build_hazard_stats 0.01180   1.42578   2     
combine pmaps            0.01065   1.42578   2     
store source model       0.00692   0.0       1     
managing sources         0.00664   0.0       1     
store source_info        0.00230   0.0       1     
saving statistics        0.00105   0.0       2     
compute stats            4.864E-04 0.0       1     
======================== ========= ========= ======