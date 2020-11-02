Event Based QA Test, Case 1
===========================

============== ====================
checksum32     4_098_937_088       
date           2020-11-02T08:41:42 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 46, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         2000                                      
truncation_level                2.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     42                                        
master_seed                     0                                         
ses_seed                        1066                                      
=============================== ==========================================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Composite source model
----------------------
====== ======================== ====
grp_id gsim                     rlzs
====== ======================== ====
0      [SiMidorikawa1999SInter] [0] 
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
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
case_09   N    2.463E-04 1         1           
case_05   N    2.439E-04 1         1           
case_03   N    2.434E-04 1         1           
case_02   N    2.410E-04 1         1           
case_06   N    2.377E-04 1         1           
case_07   N    2.367E-04 1         1           
case_08   N    2.358E-04 1         1           
case_01   N    2.341E-04 1         1           
case_04   N    2.325E-04 1         1           
case_10   N    2.174E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00237  
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       10     7.190E-04 2%     7.024E-04 7.493E-04
read_source_model  1      0.21959   nan    0.21959   0.21959  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ================================= =========
task              sent                              received 
read_source_model                                   755.95 KB
preclassical      srcs=771.41 KB srcfilter=10.03 KB 2.39 KB  
================= ================================= =========

Slowest operations
------------------
========================= ======== ========= ======
calc_46585, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.63386  1.04297   1     
composite source model    0.62910  1.04297   1     
total read_source_model   0.21959  0.22266   1     
total preclassical        0.00719  0.36328   10    
========================= ======== ========= ======