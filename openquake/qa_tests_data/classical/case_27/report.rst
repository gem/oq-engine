Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     3_403_305_238      
date           2020-03-13T11:22:12
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}   
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================== ========= ========== ==============
grp_id gsims                      distances siteparams ruptparams    
====== ========================== ========= ========== ==============
0      '[SiMidorikawa1999SInter]' rrup      vs30       hypo_depth mag
====== ========================== ========= ========== ==============

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.78947   19           19          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
case_01   0      N    1            0.00127   1.00000   1.00000     
case_12   0      N    2            1.400E-04 0.50000   2.00000     
case_14   0      N    2            1.369E-04 0.50000   2.00000     
case_15   0      N    2            1.366E-04 0.50000   2.00000     
case_13   0      N    2            1.366E-04 0.50000   2.00000     
case_02   0      N    1            1.366E-04 1.00000   1.00000     
case_03   0      N    1            1.273E-04 1.00000   1.00000     
case_04   0      N    1            1.211E-04 1.00000   1.00000     
case_06   0      N    1            1.154E-04 1.00000   1.00000     
case_10   0      N    1            1.149E-04 1.00000   1.00000     
case_08   0      N    1            1.149E-04 1.00000   1.00000     
case_05   0      N    1            1.147E-04 1.00000   1.00000     
case_09   0      N    1            1.135E-04 1.00000   1.00000     
case_07   0      N    1            1.135E-04 1.00000   1.00000     
case_11   0      N    1            1.113E-04 1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00301  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00398 NaN    0.00398 0.00398 1      
read_source_model  0.25090 NaN    0.25090 0.25090 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           1.08 MB 
preclassical      srcs=1.11 MB params=654 B srcfilter=223 B 916 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66986                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.60967   3.39062   1     
total read_source_model     0.25090   3.05469   1     
total preclassical          0.00398   0.0       1     
store source_info           0.00278   0.0       1     
aggregate curves            4.661E-04 0.0       1     
splitting/filtering sources 2.263E-04 0.0       1     
=========================== ========= ========= ======