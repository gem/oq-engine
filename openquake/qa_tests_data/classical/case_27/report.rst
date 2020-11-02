Mutex sources for Nankai, Japan, case_27
========================================

============== ====================
checksum32     541_131_823         
date           2020-11-02T08:42:21 
engine_version 3.11.0-gitd13380ddb1
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
====== ======================== ====
grp_id gsim                     rlzs
====== ======================== ====
0      [SiMidorikawa1999SInter] [0] 
1      [SiMidorikawa1999SInter] [0] 
====== ======================== ====

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
case_14           N    4.277E-04 1         2           
case_13           N    3.889E-04 1         2           
case_02           N    3.195E-04 1         1           
case_12           N    3.176E-04 1         2           
case_15           N    3.169E-04 1         2           
case_01           N    3.104E-04 1         1           
case_08           N    3.085E-04 1         1           
case_07           N    3.054E-04 1         1           
case_03           N    3.049E-04 1         1           
case_06           N    3.035E-04 1         1           
case_04           N    3.026E-04 1         1           
case_05           N    3.016E-04 1         1           
case_09           N    2.959E-04 1         1           
case_11           N    2.804E-04 1         1           
case_10           N    2.744E-04 1         1           
gs_PSE_CPCF_2_100 P    1.545E-04 1         26          
================= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00476  
P    1.545E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =======
operation-duration counts mean      stddev min       max    
preclassical       16     7.972E-04 10%    6.719E-04 0.00102
read_source_model  1      0.05253   nan    0.05253   0.05253
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
calc_46628, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.60919  0.01562   1     
composite source model    0.60425  0.01562   1     
total read_source_model   0.05253  0.01562   1     
total preclassical        0.01276  0.44531   16    
========================= ======== ========= ======