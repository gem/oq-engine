Test case for the SplitSigma modified GMPE
==========================================

============== ====================
checksum32     3_984_327_704       
date           2020-11-02T08:41:14 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 36, num_levels = 40, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              5.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.2                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     23                                        
master_seed                     0                                         
ses_seed                        24                                        
=============================== ==========================================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLt.xml <gmmLt.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLt.xml <ssmLt.xml>`_
======================= ========================

Composite source model
----------------------
====== ================================================================= ====
grp_id gsim                                                              rlzs
====== ================================================================= ====
0      [SplitSigmaGMPE]
gmpe_name = "Campbell2003"
within_absolute = 0.3 [0] 
====== ================================================================= ====

Required parameters per tectonic region type
--------------------------------------------
===== ===================================================================== ========= ========== ==========
et_id gsims                                                                 distances siteparams ruptparams
===== ===================================================================== ========= ========== ==========
0     '[SplitSigmaGMPE]\ngmpe_name = "Campbell2003"\nwithin_absolute = 0.3' rrup                 mag       
===== ===================================================================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         A    1.216E-04 36        416         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.216E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.441E-04 nan    5.441E-04 5.441E-04
read_source_model  1      0.00338   nan    0.00338   0.00338  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.72 KB 
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_46562, maxmem=0.4 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.14182   0.0       1     
composite source model    0.12367   0.0       1     
total read_source_model   0.00338   0.0       1     
total preclassical        5.441E-04 0.0       1     
========================= ========= ========= ======