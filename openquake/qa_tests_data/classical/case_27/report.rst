Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     3,403,305,238      
date           2019-10-01T07:01:09
engine_version 3.8.0-gitbd71c2f960
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
case_04   0      N    1            0.00142   1.00000   1.00000      704  
case_01   0      N    1            0.00130   1.00000   1.00000      771  
case_14   0      N    2            0.00126   1.00000   1.00000      793  
case_08   0      N    1            0.00123   1.00000   1.00000      813  
case_12   0      N    2            0.00123   1.00000   1.00000      815  
case_13   0      N    2            0.00122   1.00000   1.00000      821  
case_02   0      N    1            0.00119   1.00000   1.00000      840  
case_15   0      N    2            0.00119   1.00000   1.00000      842  
case_03   0      N    1            0.00117   1.00000   1.00000      854  
case_06   0      N    1            0.00113   1.00000   1.00000      883  
case_10   0      N    1            0.00113   1.00000   1.00000      888  
case_07   0      N    1            0.00100   1.00000   1.00000      995  
case_05   0      N    1            9.971E-04 1.00000   1.00000      1,003
case_09   0      N    1            9.680E-04 1.00000   1.00000      1,033
case_11   0      N    1            4.623E-04 0.0       0.0          0.0  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.01689   15    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.66992 NaN    0.66992 0.66992 1      
classical          0.01873 NaN    0.01873 0.01873 1      
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
calc_6632              time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.68821  4.71484   1     
total SourceReader     0.66992  3.70703   1     
total classical        0.01873  1.03125   1     
aggregate curves       0.00996  0.0       1     
make_contexts          0.00707  0.0       19    
store source_info      0.00435  3.08594   1     
get_poes               0.00175  0.0       14    
computing mean_std     0.00155  0.0       14    
====================== ======== ========= ======