Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     3,403,305,238      
date           2019-09-24T15:21:17
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 6, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================== ========= ========== ==============
grp_id gsims                      distances siteparams ruptparams    
====== ========================== ========= ========== ==============
0      '[SiMidorikawa1999SInter]' rrup      vs30       hypo_depth mag
====== ========================== ========= ========== ==============

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Subduction Interface 14           19          
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
case_01   0      N    1            0.00120   1.00000   1.00000      832  
case_04   0      N    1            0.00115   1.00000   1.00000      866  
case_12   0      N    2            0.00106   1.00000   1.00000      942  
case_03   0      N    1            0.00104   1.00000   1.00000      959  
case_15   0      N    2            0.00101   1.00000   1.00000      987  
case_08   0      N    1            0.00101   1.00000   1.00000      993  
case_14   0      N    2            0.00100   1.00000   1.00000      999  
case_02   0      N    1            9.782E-04 1.00000   1.00000      1,022
case_13   0      N    2            9.725E-04 1.00000   1.00000      1,028
case_06   0      N    1            9.346E-04 1.00000   1.00000      1,070
case_10   0      N    1            9.305E-04 1.00000   1.00000      1,075
case_07   0      N    1            9.005E-04 1.00000   1.00000      1,110
case_05   0      N    1            8.140E-04 1.00000   1.00000      1,229
case_09   0      N    1            7.982E-04 1.00000   1.00000      1,253
case_11   0      N    1            3.819E-04 0.0       0.0          0.0  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.01419   15    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
classical          0.01469 NaN    0.01469 0.01469 1      
read_source_models 0.19678 NaN    0.19678 0.19678 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ========================================== ========
task               sent                                       received
classical          group=1.08 MB src_filter=647 B param=533 B 2.66 KB 
read_source_models converter=306 B fnames=107 B               1.08 MB 
================== ========================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1824                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.19678   4.98828   1     
total classical          0.01469   0.50391   1     
aggregate curves         0.01359   0.0       1     
make_contexts            0.00592   0.0       19    
store source_info        0.00269   0.0       1     
get_poes                 0.00147   0.0       14    
computing mean_std       0.00133   0.0       14    
managing sources         2.835E-04 0.0       1     
======================== ========= ========= ======