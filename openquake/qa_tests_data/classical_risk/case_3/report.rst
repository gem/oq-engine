Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2019-07-30T15:03:57
engine_version 3.7.0-git3b3dff46da
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

  <RlzsAssoc(size=1, rlzs=1)>

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
========= ====== ==== ============ ========= ========= ======= =======
source_id grp_id code num_ruptures calc_time num_sites weight  speed  
========= ====== ==== ============ ========= ========= ======= =======
232       0      A    1,612        2.01252   5,756     1,612   800    
225       0      A    520          0.13001   1.00000   1.00000 7.69154
========= ====== ==== ============ ========= ========= ======= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.14253   15    
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ======= ======= ======= =======
operation-duration     mean    stddev  min     max     outputs
build_hazard           0.00537 0.00136 0.00444 0.00916 12     
classical_split_filter 0.55896 0.92374 0.06488 1.94395 4      
read_source_models     1.02358 NaN     1.02358 1.02358 1      
====================== ======= ======= ======= ======= =======

Fastest task
------------
taskno=4, weight=520, duration=0 s, sources="225"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1.00000 1.00000 1
weight   1.00000 NaN    1.00000 1.00000 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=5, weight=1612, duration=1 s, sources="232"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   3.57072 NaN    3.57072 3.57072 1
weight   1,612   NaN    1,612   1,612   1
======== ======= ====== ======= ======= =

Data transfer
-------------
====================== ================================================================================ ========
task                   sent                                                                             received
build_hazard           pgetter=4.56 KB hstats=780 B max_sites_disagg=60 B N=60 B individual_curves=48 B 5.07 KB 
classical_split_filter srcs=28.44 KB params=8.86 KB srcfilter=3.01 KB gsims=2.12 KB                     5.65 KB 
read_source_models     converter=314 B fnames=104 B                                                     13.75 KB
====================== ================================================================================ ========

Slowest operations
------------------
============================ ========= ========= ======
calc_15509                   time_sec  memory_mb counts
============================ ========= ========= ======
ClassicalCalculator.run      3.37285   1.89062   1     
total classical_split_filter 2.23586   0.0       4     
total read_source_models     1.02358   0.0       1     
make_contexts                0.99885   0.0       1,846 
get_poes                     0.39697   0.0       1,613 
filtering/splitting sources  0.08474   0.0       2     
total build_hazard           0.06442   1.37109   12    
read PoEs                    0.05828   1.37109   12    
building riskinputs          0.05522   0.25781   1     
saving statistics            0.00973   0.0       12    
managing sources             0.00945   0.09766   1     
store source_info            0.00200   0.0       1     
saving probability maps      0.00141   0.0       1     
compute stats                0.00126   0.0       9     
reading exposure             9.508E-04 0.0       1     
aggregate curves             7.288E-04 0.0       4     
combine pmaps                6.573E-04 0.0       12    
============================ ========= ========= ======