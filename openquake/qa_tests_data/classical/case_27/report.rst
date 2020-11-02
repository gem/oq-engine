Mutex sources for Nankai, Japan, case_27
========================================

============== ====================
checksum32     541_131_823         
date           2020-11-02T09:37:01 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 6, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                None                                      
rupture_mesh_spacing            1.0                                       
complex_fault_mesh_spacing      1.0                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      None                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1066                                      
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

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
====== ========================== ====
grp_id gsim                       rlzs
====== ========================== ====
0      '[SiMidorikawa1999SInter]' [0] 
1      '[SiMidorikawa1999SInter]' [0] 
====== ========================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ========================== ========= ========== ==============
et_id gsims                      distances siteparams ruptparams    
===== ========================== ========= ========== ==============
0     '[SiMidorikawa1999SInter]' rrup      vs30       hypo_depth mag
===== ========================== ========= ========== ==============

Slowest sources
---------------
================= ==== ========= ========= ============
source_id         code calc_time num_sites eff_ruptures
================= ==== ========= ========= ============
case_14           N    5.109E-04 1         2           
case_12           N    4.065E-04 1         2           
case_15           N    3.893E-04 1         2           
case_01           N    3.428E-04 1         1           
case_03           N    3.221E-04 1         1           
case_02           N    3.014E-04 1         1           
case_05           N    2.959E-04 1         1           
case_13           N    2.940E-04 1         2           
case_08           N    2.921E-04 1         1           
case_04           N    2.916E-04 1         1           
case_07           N    2.909E-04 1         1           
case_06           N    2.856E-04 1         1           
case_09           N    2.851E-04 1         1           
case_10           N    2.427E-04 1         1           
case_11           N    2.418E-04 1         1           
gs_PSE_CPCF_2_100 P    1.633E-04 1         26          
================= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00479  
P    1.633E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =======
operation-duration counts mean      stddev min       max    
preclassical       16     8.047E-04 15%    6.623E-04 0.00118
read_source_model  1      0.05618   nan    0.05618   0.05618
================== ====== ========= ====== ========= =======

Data transfer
-------------
================= ================================= =========
task              sent                              received 
read_source_model                                   560.14 KB
preclassical      srcs=583.31 KB srcfilter=27.42 KB 3.84 KB  
================= ================================= =========

Slowest operations
------------------
========================= ======== ========= ======
calc_47342, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.81415  0.01562   1     
composite source model    0.80962  0.01562   1     
total read_source_model   0.05618  0.01562   1     
total preclassical        0.01287  0.36719   16    
========================= ======== ========= ======