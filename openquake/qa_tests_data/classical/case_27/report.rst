Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     3,403,305,238      
date           2019-10-02T10:07:31
engine_version 3.8.0-git6f03622c6e
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
0      15        19           19          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
case_01   0      N    1            0.00168   1.00000   1.00000     
case_12   0      N    2            1.926E-04 0.50000   2.00000     
case_02   0      N    1            1.733E-04 1.00000   1.00000     
case_14   0      N    2            1.628E-04 0.50000   2.00000     
case_15   0      N    2            1.624E-04 0.50000   2.00000     
case_13   0      N    2            1.616E-04 0.50000   2.00000     
case_03   0      N    1            1.471E-04 1.00000   1.00000     
case_04   0      N    1            1.450E-04 1.00000   1.00000     
case_06   0      N    1            1.383E-04 1.00000   1.00000     
case_05   0      N    1            1.369E-04 1.00000   1.00000     
case_10   0      N    1            1.347E-04 1.00000   1.00000     
case_08   0      N    1            1.347E-04 1.00000   1.00000     
case_07   0      N    1            1.333E-04 1.00000   1.00000     
case_09   0      N    1            1.316E-04 1.00000   1.00000     
case_11   0      N    1            1.292E-04 1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.00376   15    
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       1.03379 NaN    1.03379 1.03379 1      
preclassical       0.00432 NaN    0.00432 0.00432 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ======================================== ========
task         sent                                     received
SourceReader                                          2.4 MB  
preclassical srcs=2.4 MB params=533 B srcfilter=223 B 959 B   
============ ======================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_29519             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 1.05517   5.75781   1     
total SourceReader     1.03379   3.44531   1     
store source_info      0.00550   3.34766   1     
total preclassical     0.00432   0.51562   1     
aggregate curves       3.107E-04 0.0       1     
====================== ========= ========= ======