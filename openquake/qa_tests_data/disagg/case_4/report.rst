Disaggregation with sampling
============================

============== ===================
checksum32     1,553,247,118      
date           2019-05-10T05:07:15
engine_version 3.5.0-gitbaeb4c1e35
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

  <RlzsAssoc(size=1, rlzs=2)
  0,'[ChiouYoungs2008]': [0 1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,084        2,236       
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
0      2         A    1     5     1,440        2.42492   0.0       144    
0      4         C    7     11    164          0.42247   0.0       656    
0      1         P    0     1     15           0.01440   0.0       1.50000
0      3         S    5     7     617          0.0       0.0       0.0    
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.42492   1     
C    0.42247   1     
P    0.01440   1     
S    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
read_source_models     0.04318 NaN     0.04318   0.04318 1      
classical_split_filter 0.03687 0.08928 1.512E-04 0.30246 19     
classical              0.17483 0.06956 0.09033   0.38619 16     
build_hazard_stats     0.00557 0.00225 0.00398   0.00717 2      
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
====================== ============================================================= =========
task                   sent                                                          received 
read_source_models     converter=313 B fnames=103 B                                  3.73 KB  
classical_split_filter srcs=70.91 KB params=16.37 KB srcfilter=4.28 KB gsims=3.03 KB 111.21 KB
classical              srcs=70.91 KB params=16.37 KB srcfilter=4.28 KB gsims=3.03 KB 334.68 KB
build_hazard_stats     pgetter=5.48 KB hstats=130 B N=28 B individual_curves=26 B    758 B    
====================== ============================================================= =========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              2.79725   1.01172   16    
make_contexts                1.20934   0.0       1,619 
get_poes                     0.80413   0.0       1,084 
total classical_split_filter 0.70054   0.57031   19    
filtering/splitting sources  0.29651   0.57031   3     
total read_source_models     0.04318   0.0       1     
aggregate curves             0.02951   0.0       19    
total build_hazard_stats     0.01115   0.12109   2     
combine pmaps                0.01012   0.12109   2     
managing sources             0.00449   0.0       1     
store source model           0.00299   0.0       1     
saving probability maps      0.00193   0.0       1     
store source_info            0.00150   0.0       1     
saving statistics            9.725E-04 0.0       2     
compute stats                4.177E-04 0.0       1     
============================ ========= ========= ======