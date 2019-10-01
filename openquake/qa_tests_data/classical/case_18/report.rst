Demo Classical PSHA for Vancouver Schools
=========================================

============== ===================
checksum32     572,206,371        
date           2019-10-01T07:01:18
engine_version 3.8.0-gitbd71c2f960
============== ===================

num_sites = 3, num_levels = 36, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.1               
area_source_discretization      50.0              
ground_motion_correlation_model None              
minimum_intensity               {'default': 0.002}
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(3)       3               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================================================================================== ========== ========== ==========
grp_id gsims                                                                                                                                                              distances  siteparams ruptparams
====== ================================================================================================================================================================== ========== ========== ==========
0      '[GMPETable]\ngmpe_table = "./Wcrust_high_rhypo.hdf5"' '[GMPETable]\ngmpe_table = "./Wcrust_low_rhypo.hdf5"' '[GMPETable]\ngmpe_table = "./Wcrust_med_rhypo.hdf5"' rhypo rrup            mag       
====== ================================================================================================================================================================== ========== ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=3)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.00000   2,430        2,430       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =========
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed    
========= ====== ==== ============ ========= ========= ============ =========
VICM      0      A    2,430        0.00163   3.00000   2,430        1,492,482
========= ====== ==== ============ ========= ========= ============ =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00163   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00992 NaN    0.00992 0.00992 1      
preclassical       0.00203 NaN    0.00203 0.00203 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================= ========
task         sent                                      received
SourceReader                                           4.11 KB 
preclassical gsims=157.45 KB srcs=2.16 KB params=926 B 342 B   
============ ========================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6656              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.03241   0.0       1     
total SourceReader     0.00992   0.0       1     
store source_info      0.00208   0.0       1     
total preclassical     0.00203   0.24609   1     
aggregate curves       2.177E-04 0.0       1     
====================== ========= ========= ======