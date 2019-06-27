disaggregation with a complex logic tree
========================================

============== ===================
checksum32     1,766,748,636      
date           2019-06-24T15:33:27
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 2, num_levels = 102, num_rlzs = 8

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    0                
maximum_distance                {'default': 60.0}
investigation_time              50.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            2.0              
complex_fault_mesh_spacing      2.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     24               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.25000 complex(2,2)    4               
b2        0.75000 complex(2,2)    4               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=8)>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 543          543         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 543          543         
source_model_2.xml 3      Stable Shallow Crust 1            1           
================== ====== ==================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 1,091
#tot_ruptures 1,091
#tot_weight   1,091
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight  checksum     
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
0      1         S    0     2     543          2.26177   2.00000   618     1,425,686,071
3      2         X    6     402   1            0.03162   2.00000   1.13863 953,932,561  
1      2         S    2     4     4            0.01107   2.00000   4.55452 2,443,917,473
2      1         S    4     6     543          0.0       0.0       0.0     1,425,686,071
====== ========= ==== ===== ===== ============ ========= ========= ======= =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    2.27283   3     
X    0.03162   1     
==== ========= ======

Duplicated sources
------------------
Found 2 source(s) with the same ID and 1 true duplicate(s): ['1']
Here is a fake duplicate: 2

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
build_hazard_stats     0.01598 0.00159 0.01485   0.01711 2      
classical              0.25161 0.08075 0.18811   0.38705 8      
classical_split_filter 0.03369 0.08742 2.196E-04 0.27855 10     
read_source_models     0.01595 0.00427 0.01293   0.01897 2      
====================== ======= ======= ========= ======= =======

Fastest task
------------
taskno=0, weight=543, duration=0 s, sources="2"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   543     NaN    543 543 1
======== ======= ====== === === =

Slowest task
------------
taskno=0, weight=543, duration=0 s, sources="2"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   543     NaN    543 543 1
======== ======= ====== === === =

Data transfer
-------------
====================== ============================================================ =========
task                   sent                                                         received 
build_hazard_stats     pgetter=890 B hstats=390 B N=28 B individual_curves=26 B     5.9 KB   
classical              srcs=23.29 KB params=13.2 KB gsims=2.65 KB srcfilter=2.15 KB 340.54 KB
classical_split_filter srcs=23.29 KB params=13.2 KB gsims=2.65 KB srcfilter=2.15 KB 68.39 KB 
read_source_models     converter=626 B fnames=220 B                                 13.93 KB 
====================== ============================================================ =========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              2.01288   0.50391   8     
make_contexts                1.01990   0.0       548   
get_poes                     0.51513   0.0       548   
total classical_split_filter 0.33694   0.0       10    
aggregate curves             0.03567   0.0       10    
total build_hazard_stats     0.03196   0.50781   2     
total read_source_models     0.03191   0.0       2     
read PoEs                    0.02277   0.50781   2     
filtering/splitting sources  0.01287   0.0       2     
saving probability maps      0.00986   0.0       1     
compute stats                0.00739   0.0       2     
store source model           0.00555   0.0       2     
saving statistics            0.00341   0.0       2     
managing sources             0.00285   0.0       1     
store source_info            0.00150   0.0       1     
combine pmaps                8.359E-04 0.0       2     
============================ ========= ========= ======