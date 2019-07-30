Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     3,403,305,238      
date           2019-07-30T15:04:15
engine_version 3.7.0-git3b3dff46da
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
========= ====== ==== ============ ========= ========= ======= =====
source_id grp_id code num_ruptures calc_time num_sites weight  speed
========= ====== ==== ============ ========= ========= ======= =====
case_06   0      N    1            0.00179   1.00000   1.00000 558  
case_14   0      N    2            0.00164   1.00000   1.00000 610  
case_13   0      N    2            0.00161   1.00000   1.00000 620  
case_15   0      N    2            0.00157   1.00000   1.00000 638  
case_12   0      N    2            0.00156   1.00000   1.00000 640  
case_07   0      N    1            0.00144   1.00000   1.00000 695  
case_04   0      N    1            0.00113   1.00000   1.00000 883  
case_05   0      N    1            0.00108   1.00000   1.00000 922  
case_08   0      N    1            0.00105   1.00000   1.00000 953  
case_10   0      N    1            9.665E-04 1.00000   1.00000 1,035
case_01   0      N    1            9.365E-04 1.00000   1.00000 1,068
case_02   0      N    1            8.709E-04 1.00000   1.00000 1,148
case_03   0      N    1            8.659E-04 1.00000   1.00000 1,155
case_09   0      N    1            7.341E-04 1.00000   1.00000 1,362
case_11   0      N    1            4.826E-04 0.0       0.0     0.0  
========= ====== ==== ============ ========= ========= ======= =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.01773   15    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
classical          0.02223 NaN    0.02223 0.02223 1      
read_source_models 0.18543 NaN    0.18543 0.18543 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ===================================================== ========
task               sent                                                  received
classical          srcs=1.08 MB params=533 B srcfilter=220 B gsims=170 B 2.56 KB 
read_source_models converter=306 B fnames=100 B                          1.08 MB 
================== ===================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15521               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.18543  4.26562   1     
total classical          0.02223  1.02734   1     
aggregate curves         0.01497  0.0       1     
make_contexts            0.00775  0.0       19    
store source_info        0.00684  0.0       1     
get_poes                 0.00381  0.0       14    
managing sources         0.00331  2.06250   1     
======================== ======== ========= ======