Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     3,403,305,238      
date           2019-10-01T06:32:38
engine_version 3.8.0-git66affb82eb
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      14        19           14          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
case_08   0      N    1            0.00129   1.00000   1.00000      772  
case_04   0      N    1            0.00123   1.00000   1.00000      810  
case_12   0      N    2            0.00114   1.00000   1.00000      876  
case_01   0      N    1            0.00113   1.00000   1.00000      888  
case_14   0      N    2            0.00103   1.00000   1.00000      968  
case_03   0      N    1            0.00102   1.00000   1.00000      981  
case_02   0      N    1            9.933E-04 1.00000   1.00000      1,007
case_13   0      N    2            9.878E-04 1.00000   1.00000      1,012
case_15   0      N    2            9.770E-04 1.00000   1.00000      1,024
case_06   0      N    1            9.573E-04 1.00000   1.00000      1,045
case_10   0      N    1            9.489E-04 1.00000   1.00000      1,054
case_07   0      N    1            8.972E-04 1.00000   1.00000      1,115
case_05   0      N    1            8.335E-04 1.00000   1.00000      1,200
case_09   0      N    1            8.192E-04 1.00000   1.00000      1,221
case_11   0      N    1            4.020E-04 0.0       0.0          0.0  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.01466   15    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.67553 NaN    0.67553 0.67553 1      
classical          0.01647 NaN    0.01647 0.01647 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader                                            2.38 MB 
classical    group=2.38 MB param=533 B src_filter=222 B 2.66 KB 
============ ========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6477              time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.69430  4.58594   1     
total SourceReader     0.67553  3.20703   1     
total classical        0.01647  1.03125   1     
aggregate curves       0.01142  0.0       1     
make_contexts          0.00596  0.0       19    
store source_info      0.00503  3.08594   1     
computing mean_std     0.00150  0.0       14    
get_poes               0.00148  0.0       14    
====================== ======== ========= ======