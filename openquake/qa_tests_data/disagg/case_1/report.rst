QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     1,811,660,702      
date           2019-05-10T05:07:17
engine_version 3.5.0-gitbaeb4c1e35
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
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
1      2         A    1     5     1,440        2.72428   0.0       144    
2      3         S    5     7     617          1.29854   0.0       617    
3      4         C    7     11    164          0.70734   0.0       656    
0      1         P    0     1     15           0.03299   0.0       1.50000
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.72428   1     
C    0.70734   1     
P    0.03299   1     
S    1.29854   1     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
read_source_models     0.03659 NaN     0.03659   0.03659 1      
classical_split_filter 0.23668 0.30875 1.538E-04 0.71378 7      
classical              1.06627 0.00383 1.06185   1.06867 3      
build_hazard_stats     0.01022 0.00377 0.00756   0.01289 2      
====================== ======= ======= ========= ======= =======

Fastest task
------------
taskno=1, weight=1440, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   144     NaN    144 144 1
======== ======= ====== === === =

Slowest task
------------
taskno=3, weight=164, duration=0 s, sources="3"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   656     NaN    656 656 1
======== ======= ====== === === =

Data transfer
-------------
====================== =========================================================== =========
task                   sent                                                        received 
read_source_models     converter=313 B fnames=103 B                                4.05 KB  
classical_split_filter srcs=25.75 KB params=5.74 KB srcfilter=1.5 KB gsims=1.06 KB 211.25 KB
classical              srcs=25.75 KB params=5.74 KB srcfilter=1.5 KB gsims=1.06 KB 517 KB   
build_hazard_stats     pgetter=5.84 KB hstats=130 B N=28 B individual_curves=26 B  684 B    
====================== =========================================================== =========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              3.19881   0.22656   3     
make_contexts                1.70807   0.0       2,236 
total classical_split_filter 1.65677   0.18359   7     
get_poes                     0.99174   0.0       2,236 
filtering/splitting sources  0.04078   0.0       4     
total read_source_models     0.03659   0.0       1     
aggregate curves             0.02090   0.0       7     
total build_hazard_stats     0.02045   0.37891   2     
combine pmaps                0.01897   0.37891   2     
saving probability maps      0.00727   0.0       1     
managing sources             0.00420   0.0       1     
store source model           0.00394   0.0       1     
store source_info            0.00135   0.0       1     
saving statistics            8.740E-04 0.0       2     
compute stats                7.973E-04 0.0       1     
============================ ========= ========= ======