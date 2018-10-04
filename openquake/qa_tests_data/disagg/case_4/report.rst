Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2018-10-04T15:36:24
engine_version 3.3.0-gitf22d3f2c70
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
source                  `source_model.xml <source_model.xml>`_                      
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
0      1         P    0     1     15           0.01703   3.147E-05  1.00000   1         1.50000
0      2         A    1     5     1,440        1.50065   2.32681    96        96        144    
0      3         S    5     7     617          0.0       0.0        0.0       0         0.0    
0      4         C    7     11    164          0.70279   0.00175    10        10        656    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.50065   1     
C    0.70279   1     
P    0.01703   1     
S    0.0       1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.05669 NaN     0.05669 0.05669 1      
split_filter       0.04947 NaN     0.04947 0.04947 1      
classical          0.28247 0.48919 0.06159 1.48741 8      
build_hazard_stats 0.00589 0.00183 0.00460 0.00718 2      
================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=3, weight=88, duration=0 s, sources="4"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   88      NaN    88  88  1
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=141, duration=1 s, sources="1 2"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       94
weight   1.50000 0.0    1.50000 1.50000 94
======== ======= ====== ======= ======= ==

Data transfer
-------------
================== =========================================================================== ========
task               sent                                                                        received
read_source_models monitor=0 B fnames=0 B converter=0 B                                        3.63 KB 
split_filter       srcs=3.32 KB monitor=439 B srcfilter=253 B sample_factor=21 B seed=15 B     24.73 KB
classical          group=31.64 KB param=6.77 KB monitor=2.7 KB src_filter=1.72 KB gsims=1016 B 7.03 KB 
build_hazard_stats pgetter=5.04 KB monitor=708 B hstats=134 B                                  684 B   
================== =========================================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total classical          2.25973   0.98438   8     
make_contexts            0.88306   0.0       1,619 
iter_ruptures            0.86864   0.0       107   
get_poes                 0.45273   0.0       1,084 
updating source_info     0.06157   0.25781   1     
total read_source_models 0.05669   0.0       1     
total split_filter       0.04947   0.67188   1     
store source_info        0.02278   0.0       8     
total build_hazard_stats 0.01178   0.53906   2     
combine pmaps            0.01091   0.53906   2     
managing sources         0.00578   0.0       1     
aggregate curves         0.00262   0.0       8     
saving statistics        0.00152   0.0       2     
saving probability maps  0.00145   0.0       1     
compute mean             3.238E-04 0.0       1     
======================== ========= ========= ======