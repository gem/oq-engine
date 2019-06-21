Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2019-06-21T09:41:49
engine_version 3.6.0-git17fd0581aa
============== ===================

num_sites = 12, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

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
====== =================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,'[ChiouYoungs2008]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,613        33,831      
================ ====== ==================== ============ ============

Exposure model
--------------
=========== ==
#assets     13
#taxonomies 4 
=========== ==

======== ======= ======= === === ========= ==========
taxonomy mean    stddev  min max num_sites num_assets
W        1.00000 0.0     1   1   5         5         
A        1.00000 0.0     1   1   4         4         
DS       2.00000 NaN     2   2   1         2         
UFB      1.00000 0.0     1   1   2         2         
*ALL*    1.08333 0.28868 1   2   12        13        
======== ======= ======= === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
0      232       A    41    45    1,612        1.98932   6.00000   2,191 
0      225       A    38    41    520          0.16055   2.00000   266   
0      8         A    0     4     4,832        0.0       0.0       0.0   
0      59        A    16    20    750          0.0       0.0       0.0   
0      57        A    12    16    840          0.0       0.0       0.0   
0      42        A    8     12    1,755        0.0       0.0       0.0   
0      359       A    59    63    2,314        0.0       0.0       0.0   
0      306       A    55    59    1,768        0.0       0.0       0.0   
0      299       A    51    55    710          0.0       0.0       0.0   
0      27        A    4     8     1,482        0.0       0.0       0.0   
0      253       A    45    51    3,058        0.0       0.0       0.0   
0      137       A    34    38    2,072        0.0       0.0       0.0   
0      135       A    30    34    3,285        0.0       0.0       0.0   
0      125       A    26    30    8,274        0.0       0.0       0.0   
0      101       A    20    26    559          0.0       0.0       0.0   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.14987   15    
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
build_hazard_stats     0.00627 0.00182 0.00338 0.00843 12     
classical              1.95599 NaN     1.95599 1.95599 1      
classical_split_filter 0.11459 0.06573 0.05783 0.18660 3      
read_source_models     1.07933 NaN     1.07933 1.07933 1      
====================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=5, weight=1612, duration=0 s, sources="225"

======== ======= ====== ===== ===== =
variable mean    stddev min   max   n
======== ======= ====== ===== ===== =
nsites   1.00000 NaN    1     1     1
weight   1,612   NaN    1,612 1,612 1
======== ======= ====== ===== ===== =

Slowest task
------------
taskno=4, weight=520, duration=0 s, sources="137"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   520     NaN    520 520 1
======== ======= ====== === === =

Data transfer
-------------
====================== ============================================================ ========
task                   sent                                                         received
build_hazard_stats     pgetter=4.56 KB hstats=780 B N=168 B individual_curves=156 B 5.07 KB 
classical              srcs=60.1 KB params=8.92 KB srcfilter=3.22 KB gsims=2.27 KB  2.19 KB 
classical_split_filter srcs=60.1 KB params=8.92 KB srcfilter=3.22 KB gsims=2.27 KB  35.34 KB
read_source_models     converter=313 B fnames=111 B                                 13.71 KB
====================== ============================================================ ========

Slowest operations
------------------
============================ ========= ========= ======
operation                    time_sec  memory_mb counts
============================ ========= ========= ======
total classical              1.95599   0.66406   1     
total read_source_models     1.07933   0.0       1     
make_contexts                1.07851   0.0       1,846 
get_poes                     0.42686   0.0       1,613 
total classical_split_filter 0.34377   0.42578   3     
filtering/splitting sources  0.08143   0.42578   2     
total build_hazard_stats     0.07525   1.42578   12    
read PoEs                    0.06726   1.42578   12    
building riskinputs          0.03020   0.0       1     
managing sources             0.01354   0.0       1     
saving statistics            0.00633   0.0       12    
store source model           0.00465   0.0       1     
store source_info            0.00173   0.0       1     
saving probability maps      0.00171   0.0       1     
compute stats                0.00137   0.0       9     
aggregate curves             0.00103   0.0       3     
combine pmaps                7.629E-04 0.0       12    
reading exposure             4.876E-04 0.0       1     
============================ ========= ========= ======