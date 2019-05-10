Demo Classical PSHA for Vancouver Schools
=========================================

============== ===================
checksum32     3,805,160,323      
date           2019-05-10T05:08:05
engine_version 3.5.0-gitbaeb4c1e35
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
minimum_intensity               {}                
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
====== ============================================================================================================================================================ ========== ========== ==========
grp_id gsims                                                                                                                                                        distances  siteparams ruptparams
====== ============================================================================================================================================================ ========== ========== ==========
0      '[GMPETable]\ngmpe_table = "Wcrust_high_rhypo.hdf5"' '[GMPETable]\ngmpe_table = "Wcrust_low_rhypo.hdf5"' '[GMPETable]\ngmpe_table = "Wcrust_med_rhypo.hdf5"' rhypo rrup            mag       
====== ============================================================================================================================================================ ========== ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,'[GMPETable]\ngmpe_table = "Wcrust_high_rhypo.hdf5"': [2]
  0,'[GMPETable]\ngmpe_table = "Wcrust_low_rhypo.hdf5"': [0]
  0,'[GMPETable]\ngmpe_table = "Wcrust_med_rhypo.hdf5"': [1]>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== ============ ============
source_model              grp_id trt                  eff_ruptures tot_ruptures
========================= ====== ==================== ============ ============
vancouver_area_source.xml 0      Active Shallow Crust 2,430        2,430       
========================= ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
0      VICM      A    0     8     2,430        0.00183   3.00000   420   
====== ========= ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00183   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00994 NaN    0.00994 0.00994 1      
preclassical       0.00216 NaN    0.00216 0.00216 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ========================================================= ========
task               sent                                                      received
read_source_models converter=313 B fnames=116 B                              2.51 KB 
preclassical       gsims=157.44 KB srcs=2.16 KB params=887 B srcfilter=219 B 344 B   
================== ========================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.00994   0.0       1     
managing sources         0.00443   0.0       1     
total preclassical       0.00216   0.0       1     
store source_info        0.00173   0.0       1     
aggregate curves         1.469E-04 0.0       1     
======================== ========= ========= ======