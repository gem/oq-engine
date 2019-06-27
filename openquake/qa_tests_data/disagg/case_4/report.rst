Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2019-06-24T15:33:26
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 2, num_levels = 38, num_rlzs = 2

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
b1        0.50000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== =========== ======================= =================
grp_id gsims               distances   siteparams              ruptparams       
====== =================== =========== ======================= =================
0      '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=2)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,084        2,236       
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
0      2         A    1     5     1,440        2.89806   1.00000   1,440  3,959,327,310
0      4         C    7     11    164          0.47244   1.00000   164    2,770,673,874
0      1         P    0     1     15           0.01567   1.00000   15     1,116,294,081
0      3         S    5     7     617          0.0       0.0       0.0    4,249,039,070
====== ========= ==== ===== ===== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.89806   1     
C    0.47244   1     
P    0.01567   1     
S    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
build_hazard_stats     0.00497 0.00207 0.00351   0.00644 2      
classical              0.23937 0.09288 0.11447   0.46228 14     
classical_split_filter 0.04210 0.09433 1.826E-04 0.29208 17     
read_source_models     0.04912 NaN     0.04912   0.04912 1      
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
====================== ============================================================= =========
task                   sent                                                          received 
build_hazard_stats     pgetter=794 B hstats=130 B N=28 B individual_curves=26 B      883 B    
classical              srcs=76.15 KB params=14.73 KB srcfilter=3.87 KB gsims=2.72 KB 336.83 KB
classical_split_filter srcs=76.15 KB params=14.73 KB srcfilter=3.87 KB gsims=2.72 KB 110.26 KB
read_source_models     converter=313 B fnames=103 B                                  3.74 KB  
====================== ============================================================= =========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              3.35125   1.04297   14    
make_contexts                1.37502   0.0       1,619 
get_poes                     0.94961   0.0       1,084 
total classical_split_filter 0.71569   0.50781   17    
filtering/splitting sources  0.31810   0.50781   3     
total read_source_models     0.04912   0.0       1     
aggregate curves             0.02599   0.0       17    
total build_hazard_stats     0.00995   0.50781   2     
read PoEs                    0.00887   0.50781   2     
managing sources             0.00376   0.0       1     
store source model           0.00302   0.0       1     
saving probability maps      0.00227   0.0       1     
store source_info            0.00169   0.0       1     
saving statistics            0.00107   0.0       2     
compute stats                1.421E-04 0.0       1     
combine pmaps                7.892E-05 0.0       2     
============================ ========= ========= ======