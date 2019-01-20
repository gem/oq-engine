Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2019-01-20T07:36:51
engine_version 3.4.0-git452d0c6835
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
0      1         P    0     1     15           0.00802   2.122E-05  1.00000   1         1.50000
0      2         A    1     5     1,440        1.43235   1.26146    96        96        144    
0      3         S    5     7     617          0.0       0.0        0.0       0         0.0    
0      4         C    7     11    164          0.28221   2.05697    10        10        656    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.43235   1     
C    0.28221   1     
P    0.00802   1     
S    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.03083 NaN       0.03083 0.03083 1      
split_filter       0.24432 NaN       0.24432 0.24432 1      
classical          0.17322 0.32700   0.02070 1.04109 10     
build_hazard_stats 0.00454 4.690E-04 0.00420 0.00487 2      
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
split_filter       srcs=3.34 KB srcfilter=253 B seed=14 B                         99.54 KB
classical          group=101.73 KB src_filter=8.78 KB param=8.05 KB gsims=1.24 KB 8.83 KB 
build_hazard_stats pgetter=5.23 KB hstats=134 B individual_curves=26 B            684 B   
================== ============================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          1.73216   0.82812   10    
make_contexts            0.78682   0.0       1,619 
get_poes                 0.42778   0.0       1,084 
total split_filter       0.24432   2.34766   1     
total read_source_models 0.03083   0.64062   1     
store source_info        0.02372   0.0       10    
total build_hazard_stats 0.00907   1.42188   2     
managing sources         0.00826   0.0       1     
combine pmaps            0.00791   1.40234   2     
aggregate curves         0.00270   0.0       10    
store source model       0.00256   0.0       1     
saving probability maps  0.00122   0.0       1     
saving statistics        0.00111   0.0       2     
compute mean             4.878E-04 0.0       1     
======================== ========= ========= ======