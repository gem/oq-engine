Demo Classical PSHA for Vancouver Schools
=========================================

============== ====================
checksum32     3_835_829_256       
date           2020-11-02T09:37:39 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 3, num_levels = 36, num_rlzs = 3

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 400.0), (10.0, 400.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      50.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {'default': 0.002}                        
random_seed                     23                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `nbc_asc_logic_tree.xml <nbc_asc_logic_tree.xml>`_          
job_ini                 `job.ini <job.ini>`_                                        
sites                   `vancouver_school_sites.csv <vancouver_school_sites.csv>`_  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ====================================================== ====
grp_id gsim                                                   rlzs
====== ====================================================== ====
0      '[GMPETable]\ngmpe_table = "./Wcrust_high_rhypo.hdf5"' [2] 
0      '[GMPETable]\ngmpe_table = "./Wcrust_low_rhypo.hdf5"'  [0] 
0      '[GMPETable]\ngmpe_table = "./Wcrust_med_rhypo.hdf5"'  [1] 
====== ====================================================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ================================================================================================================================================================== ========= ========== ==========
et_id gsims                                                                                                                                                              distances siteparams ruptparams
===== ================================================================================================================================================================== ========= ========== ==========
0     '[GMPETable]\ngmpe_table = "./Wcrust_high_rhypo.hdf5"' '[GMPETable]\ngmpe_table = "./Wcrust_low_rhypo.hdf5"' '[GMPETable]\ngmpe_table = "./Wcrust_med_rhypo.hdf5"' rhypo                mag       
===== ================================================================================================================================================================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
VICM      A    1.209E-04 3         2_430       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.209E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.412E-04 nan    5.412E-04 5.412E-04
read_source_model  1      0.00350   nan    0.00350   0.00350  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.8 KB  
preclassical           242 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47374, maxmem=0.3 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.08409   0.0       1     
composite source model    0.07901   0.0       1     
total read_source_model   0.00350   0.0       1     
total preclassical        5.412E-04 0.0       1     
========================= ========= ========= ======