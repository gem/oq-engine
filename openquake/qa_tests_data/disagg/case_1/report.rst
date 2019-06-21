QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     1,811,660,702      
date           2019-06-21T09:42:00
engine_version 3.6.0-git17fd0581aa
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
#tot_weight   2,236
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
1      2         A    1     5     1,440        2.99916   1.00000   1,440 
2      3         S    5     7     617          1.47579   1.00000   617   
3      4         C    7     11    164          0.61824   1.00000   164   
0      1         P    0     1     15           0.03497   1.00000   15    
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.99916   1     
C    0.61824   1     
P    0.03497   1     
S    1.47579   1     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ========= ========= ======= =======
operation-duration     mean    stddev    min       max     outputs
build_hazard_stats     0.01244 2.458E-04 0.01227   0.01262 2      
classical              1.18685 0.04742   1.13282   1.22155 3      
classical_split_filter 0.27411 0.36704   1.621E-04 0.87737 7      
read_source_models     0.04194 NaN       0.04194   0.04194 1      
====================== ======= ========= ========= ======= =======

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
classical              srcs=25.84 KB params=5.74 KB srcfilter=1.5 KB gsims=1.06 KB 517.05 KB
classical_split_filter srcs=25.84 KB params=5.74 KB srcfilter=1.5 KB gsims=1.06 KB 211.41 KB
read_source_models     converter=313 B fnames=103 B                                4.05 KB  
====================== =========================================================== =========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              3.56054   0.17578   3     
total classical_split_filter 1.91879   0.21484   7     
make_contexts                1.89106   0.0       2,236 
get_poes                     1.10557   0.0       2,236 
filtering/splitting sources  0.29611   0.0       4     
total read_source_models     0.04194   0.0       1     
aggregate curves             0.02700   0.0       7     
total build_hazard_stats     0.02488   1.28516   2     
read PoEs                    0.02336   1.28516   2     
saving probability maps      0.01046   0.0       1     
store source model           0.00673   0.0       1     
managing sources             0.00374   0.0       1     
store source_info            0.00172   0.0       1     
saving statistics            0.00104   0.0       2     
combine pmaps                2.320E-04 0.0       2     
compute stats                1.850E-04 0.0       1     
============================ ========= ========= ======