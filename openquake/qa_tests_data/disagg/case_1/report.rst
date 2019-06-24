QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     1,811,660,702      
date           2019-06-24T15:33:28
engine_version 3.6.0-git4b6205639c
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

  <RlzsAssoc(size=4, rlzs=1)>

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
#tot_weight   2,236
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
1      2         A    1     5     1,440        3.04646   1.00000   1,440  3,959,327,310
2      3         S    5     7     617          1.48465   1.00000   617    4,249,039,070
3      4         C    7     11    164          0.64219   1.00000   164    2,770,673,874
0      1         P    0     1     15           0.03528   1.00000   15     1,116,294,081
====== ========= ==== ===== ===== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    3.04646   1     
C    0.64219   1     
P    0.03528   1     
S    1.48465   1     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
build_hazard_stats     0.00971 0.00164 0.00854   0.01087 2      
classical              1.20894 0.05124 1.15039   1.24557 3      
classical_split_filter 0.27687 0.37264 1.659E-04 0.90421 7      
read_source_models     0.04190 NaN     0.04190   0.04190 1      
====================== ======= ======= ========= ======= =======

Fastest task
------------
taskno=1, weight=1440, duration=0 s, sources="1"

======== ======= ====== ===== ===== =
variable mean    stddev min   max   n
======== ======= ====== ===== ===== =
nsites   1.00000 NaN    1     1     1
weight   1,440   NaN    1,440 1,440 1
======== ======= ====== ===== ===== =

Slowest task
------------
taskno=3, weight=164, duration=0 s, sources="3"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   164     NaN    164 164 1
======== ======= ====== === === =

Data transfer
-------------
====================== =========================================================== =========
task                   sent                                                        received 
build_hazard_stats     pgetter=778 B hstats=130 B N=28 B individual_curves=26 B    825 B    
classical              srcs=25.98 KB params=5.74 KB srcfilter=1.5 KB gsims=1.06 KB 517.14 KB
classical_split_filter srcs=25.98 KB params=5.74 KB srcfilter=1.5 KB gsims=1.06 KB 211.59 KB
read_source_models     converter=313 B fnames=103 B                                4.07 KB  
====================== =========================================================== =========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              3.62682   0.42578   3     
total classical_split_filter 1.93806   0.36328   7     
make_contexts                1.92295   0.0       2,236 
get_poes                     1.11067   0.0       2,236 
filtering/splitting sources  0.30050   0.25000   4     
total read_source_models     0.04190   0.0       1     
aggregate curves             0.02373   1.03125   7     
total build_hazard_stats     0.01941   1.53125   2     
read PoEs                    0.01842   1.53125   2     
saving probability maps      0.00968   0.0       1     
store source model           0.00696   0.51172   1     
managing sources             0.00394   0.0       1     
store source_info            0.00151   0.0       1     
saving statistics            0.00113   0.0       2     
combine pmaps                1.209E-04 0.0       2     
compute stats                9.918E-05 0.0       1     
============================ ========= ========= ======