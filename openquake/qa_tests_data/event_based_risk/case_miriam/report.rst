Virtual Island - City C, 2 SES, grid=0.1
========================================

============== ====================
checksum32     2_344_008_924       
date           2020-11-02T09:36:40 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 281, num_levels = 50, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              5.0                                       
ses_per_logic_tree_path         2                                         
truncation_level                4.0                                       
rupture_mesh_spacing            10.0                                      
complex_fault_mesh_spacing      10.0                                      
width_of_mfd_bin                0.2                                       
area_source_discretization      None                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1024                                      
master_seed                     100                                       
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
====== =========================== ====
grp_id gsim                        rlzs
====== =========================== ====
0      '[AkkarBommer2010]'         [0] 
1      '[AtkinsonBoore2003SInter]' [0] 
====== =========================== ====

Required parameters per tectonic region type
--------------------------------------------
===== =========================== ========= ========== ==============
et_id gsims                       distances siteparams ruptparams    
===== =========================== ========= ========== ==============
0     '[AkkarBommer2010]'         rjb       vs30       mag rake      
1     '[AtkinsonBoore2003SInter]' rrup      vs30       hypo_depth mag
===== =========================== ========= ========== ==============

Exposure model
--------------
=========== ===
#assets     548
#taxonomies 11 
=========== ===

========== ========== ======= ====== === === =========
taxonomy   num_assets mean    stddev min max num_sites
MS-FLSB-2  12         1.25000 34%    1   2   15       
MS-SLSB-1  11         1.54545 57%    1   4   17       
MC-RLSB-2  39         1.25641 69%    1   6   49       
W-SLFB-1   83         1.26506 40%    1   3   105      
MR-RCSB-2  171        1.45614 54%    1   6   249      
MC-RCSB-1  21         1.28571 42%    1   3   27       
W-FLFB-2   54         1.22222 40%    1   3   66       
PCR-RCSM-5 2          1.00000 0%     1   1   2        
MR-SLSB-1  5          1.00000 0%     1   1   5        
A-SPSB-1   8          1.25000 34%    1   2   10       
PCR-SLSB-1 3          1.00000 0%     1   1   3        
*ALL*      1_971      0.27803 302%   0   10  548      
========== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
D         C    0.00157   281       3_345       
F         C    0.00155   281       2_348       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.00312  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       2      0.00207 0%     0.00206 0.00208
read_source_model  1      0.00484 nan    0.00484 0.00484
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model                                 2.09 KB 
preclassical      srcfilter=33.41 KB srcs=2.64 KB 478 B   
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47314, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.24257  0.24219   1     
composite source model    0.60199  0.02734   1     
reading exposure          0.05534  0.00391   1     
total read_source_model   0.00484  0.0       1     
total preclassical        0.00414  0.45312   2     
========================= ======== ========= ======