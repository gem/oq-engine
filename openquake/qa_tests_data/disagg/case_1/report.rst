QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ===================
checksum32     1,811,660,702      
date           2018-12-13T12:57:09
engine_version 3.3.0-git68d7d11268
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
0      1         P    0     1     15           0.02424   2.050E-05  1.00000   1         1.50000
1      2         A    1     5     1,440        1.95264   1.27272    96        96        144    
2      3         S    5     7     617          1.09181   0.00118    10        10        617    
3      4         C    7     11    164          0.39098   2.04079    10        10        656    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.95264   1     
C    0.39098   1     
P    0.02424   1     
S    1.09181   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.04064 NaN     0.04064 0.04064 1      
split_filter       0.24350 NaN     0.24350 0.24350 1      
classical          0.57812 0.70828 0.02480 1.95785 6      
build_hazard_stats 0.00817 0.00321 0.00589 0.01044 2      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=6, weight=1, duration=0 s, sources="4"

======== ======= ====== ======= === =
variable mean    stddev min     max n
======== ======= ====== ======= === =
nsites   1.00000 0.0    1       1   6
weight   51      29     4.00000 80  6
======== ======= ====== ======= === =

Slowest task
------------
taskno=6, weight=144, duration=1 s, sources="4"

======== ======= ====== ======= === =
variable mean    stddev min     max n
======== ======= ====== ======= === =
nsites   1.00000 0.0    1       1   6
weight   51      29     4.00000 80  6
======== ======= ====== ======= === =

Data transfer
-------------
================== =========================================================== =========
task               sent                                                        received 
read_source_models converter=388 B fnames=103 B                                3.85 KB  
split_filter       srcs=3.31 KB srcfilter=253 B seed=14 B                      100.72 KB
classical          group=98.62 KB src_filter=5.27 KB param=4.83 KB gsims=762 B 5.21 KB  
build_hazard_stats pgetter=5.43 KB hstats=134 B                                684 B    
================== =========================================================== =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          3.46872   0.27344   6     
make_contexts            1.79610   0.0       2,236 
get_poes                 0.97562   0.0       2,236 
iter_ruptures            0.66579   0.0       117   
total split_filter       0.24350   0.55469   1     
total read_source_models 0.04064   0.18359   1     
store source_info        0.01863   0.0       6     
total build_hazard_stats 0.01633   0.55469   2     
combine pmaps            0.01545   0.55469   2     
managing sources         0.00757   0.0       1     
saving probability maps  0.00422   0.0       1     
store source model       0.00401   0.0       1     
aggregate curves         0.00175   0.0       6     
saving statistics        0.00147   0.0       2     
compute mean             2.735E-04 0.0       1     
======================== ========= ========= ======