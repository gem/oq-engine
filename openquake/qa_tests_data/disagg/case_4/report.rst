Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2018-12-13T12:57:07
engine_version 3.3.0-git68d7d11268
============== ===================

num_sites = 2, num_levels = 38

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    2                
maximum_distance                {'default': 40.0}
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
=============================== =================

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
b1        0.50000 trivial(1)      2/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=2)
  0,ChiouYoungs2008(): [0 1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,084        2,236       
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         P    0     1     15           0.01463   3.052E-05  1.00000   1         1.50000
0      2         A    1     5     1,440        1.49448   2.14027    96        96        144    
0      3         S    5     7     617          0.0       0.0        0.0       0         0.0    
0      4         C    7     11    164          0.40080   2.49570    10        10        656    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.49448   1     
C    0.40080   1     
P    0.01463   1     
S    0.0       1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.04366 NaN       0.04366 0.04366 1      
split_filter       0.30065 NaN       0.30065 0.30065 1      
classical          0.19209 0.34157   0.02078 1.10568 10     
build_hazard_stats 0.00803 9.178E-04 0.00738 0.00868 2      
================== ======= ========= ======= ======= =======

Fastest task
------------
taskno=10, weight=88, duration=0 s, sources="4"

======== ======= ====== ======= === =
variable mean    stddev min     max n
======== ======= ====== ======= === =
nsites   1.00000 0.0    1       1   3
weight   29      24     4.00000 52  3
======== ======= ====== ======= === =

Slowest task
------------
taskno=10, weight=99, duration=1 s, sources="4"

======== ======= ====== ======= === =
variable mean    stddev min     max n
======== ======= ====== ======= === =
nsites   1.00000 0.0    1       1   3
weight   29      24     4.00000 52  3
======== ======= ====== ======= === =

Data transfer
-------------
================== ============================================================== ========
task               sent                                                           received
read_source_models converter=388 B fnames=103 B                                   3.63 KB 
split_filter       srcs=3.34 KB srcfilter=253 B seed=14 B                         98.58 KB
classical          group=101.28 KB src_filter=8.78 KB param=8.05 KB gsims=1.24 KB 8.73 KB 
build_hazard_stats pgetter=5.03 KB hstats=134 B                                   684 B   
================== ============================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          1.92092   0.45312   10    
make_contexts            0.91668   0.0       1,619 
iter_ruptures            0.50597   0.0       107   
get_poes                 0.47048   0.0       1,084 
total split_filter       0.30065   0.85156   1     
total read_source_models 0.04366   0.21094   1     
store source_info        0.02519   0.0       10    
total build_hazard_stats 0.01606   0.14844   2     
combine pmaps            0.01442   0.14844   2     
managing sources         0.00824   0.0       1     
aggregate curves         0.00249   0.0       10    
store source model       0.00233   0.0       1     
saving probability maps  0.00143   0.0       1     
saving statistics        0.00122   0.0       2     
compute mean             6.218E-04 0.0       1     
======================== ========= ========= ======