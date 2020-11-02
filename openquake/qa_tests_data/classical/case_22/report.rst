Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ====================
checksum32     2_585_246_824       
date           2020-11-02T09:36:49 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 21, num_levels = 114, num_rlzs = 4

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            4.0                                       
complex_fault_mesh_spacing      4.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     23                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `sites.csv <sites.csv>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ================================== ====
grp_id gsim                               rlzs
====== ================================== ====
0      '[AbrahamsonSilva1997]'            [0] 
0      '[CampbellBozorgnia2003NSHMP2007]' [1] 
0      '[SadighEtAl1997]'                 [2] 
0      '[YoungsEtAl1997SInterNSHMP2008]'  [3] 
====== ================================== ====

Required parameters per tectonic region type
--------------------------------------------
===== =============================================================================================================== ========= ========== =======================
et_id gsims                                                                                                           distances siteparams ruptparams             
===== =============================================================================================================== ========= ========== =======================
0     '[AbrahamsonSilva1997]' '[CampbellBozorgnia2003NSHMP2007]' '[SadighEtAl1997]' '[YoungsEtAl1997SInterNSHMP2008]' rjb rrup  vs30       dip hypo_depth mag rake
===== =============================================================================================================== ========= ========== =======================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
2         M    7.277E-04 21        1_104       
1         M    4.165E-04 3         160         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
M    0.00114  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       2      0.00117 20%    9.277E-04 0.00140
read_source_model  2      0.00171 8%     0.00158   0.00185
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model converter=664 B fname=213 B    6.57 KB 
preclassical      srcs=6.19 KB srcfilter=4.03 KB 478 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47324, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.02429  0.0       1     
composite source model    1.01466  0.0       1     
total read_source_model   0.00343  0.41406   2     
total preclassical        0.00233  0.41797   2     
========================= ======== ========= ======