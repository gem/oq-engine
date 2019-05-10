disaggregation with a complex logic tree
========================================

============== ===================
checksum32     1,766,748,636      
date           2019-05-10T05:07:16
engine_version 3.5.0-gitbaeb4c1e35
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

  <RlzsAssoc(size=8, rlzs=8)
  0,'[BooreAtkinson2008]': [0 1]
  0,'[ChiouYoungs2008]': [2 3]
  1,'[AkkarBommer2010]': [0 2]
  1,'[ChiouYoungs2008]': [1 3]
  2,'[BooreAtkinson2008]': [4 5]
  2,'[ChiouYoungs2008]': [6 7]
  3,'[AkkarBommer2010]': [4 6]
  3,'[ChiouYoungs2008]': [5 7]>

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
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
0      1         S    0     2     543          2.04273   0.0       767    
2      1         S    4     6     543          2.03800   0.0       767    
3      2         X    6     402   1            0.02751   0.0       1.41421
1      2         S    2     4     4            0.01373   0.0       5.65685
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    4.09446   3     
X    0.02751   1     
==== ========= ======

Duplicated sources
------------------
['1']
Found 2 source(s) with the same ID and 1 true duplicate(s)
Here is a fake duplicate: 2

Information about the tasks
---------------------------
====================== ======= ======= ========= ======= =======
operation-duration     mean    stddev  min       max     outputs
read_source_models     0.01260 0.00321 0.01033   0.01487 2      
classical_split_filter 0.04912 0.11720 3.018E-04 0.34386 15     
classical              0.28795 0.08214 0.18753   0.40785 12     
build_hazard_stats     0.01564 0.00129 0.01473   0.01655 2      
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
taskno=1, weight=543, duration=0 s, sources="1"

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
read_source_models     converter=626 B fnames=220 B                                 13.92 KB 
classical_split_filter srcs=29.32 KB params=19.8 KB gsims=3.98 KB srcfilter=3.21 KB 95.26 KB 
classical              srcs=29.32 KB params=19.8 KB gsims=3.98 KB srcfilter=3.21 KB 349.23 KB
build_hazard_stats     pgetter=11.4 KB hstats=390 B N=28 B individual_curves=26 B   5.96 KB  
====================== ============================================================ =========

Slowest operations
------------------
============================ ======== ========= ======
operation                    time_sec memory_mb counts
============================ ======== ========= ======
total classical              3.45540  0.50391   12    
make_contexts                1.82519  0.0       1,091 
get_poes                     0.96291  0.0       1,091 
total classical_split_filter 0.73683  0.20703   15    
total build_hazard_stats     0.03128  0.0       2     
aggregate curves             0.02952  0.51172   15    
total read_source_models     0.02520  0.0       2     
combine pmaps                0.02266  0.0       2     
filtering/splitting sources  0.01866  0.0       3     
compute stats                0.00799  0.0       2     
saving probability maps      0.00735  0.0       1     
store source model           0.00572  0.0       2     
managing sources             0.00287  0.0       1     
saving statistics            0.00253  0.0       2     
store source_info            0.00135  0.0       1     
============================ ======== ========= ======