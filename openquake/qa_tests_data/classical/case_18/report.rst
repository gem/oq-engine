Demo Classical PSHA for Vancouver Schools
=========================================

============== ===================
checksum32     2_503_288_659      
date           2020-01-16T05:31:59
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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
====== ================================================================================================================================================================== ========= ========== ==========
grp_id gsims                                                                                                                                                              distances siteparams ruptparams
====== ================================================================================================================================================================== ========= ========== ==========
0      '[GMPETable]\ngmpe_table = "./Wcrust_high_rhypo.hdf5"' '[GMPETable]\ngmpe_table = "./Wcrust_low_rhypo.hdf5"' '[GMPETable]\ngmpe_table = "./Wcrust_med_rhypo.hdf5"' rhypo                mag       
====== ================================================================================================================================================================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=3)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.03704   2_430        2_430       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
VICM      0      A    2_430        0.00433   0.03704   2_430       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00433  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.01061 NaN    0.01061 0.01061 1      
preclassical       0.01853 NaN    0.01853 0.01853 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader                                             3.32 KB 
preclassical gsims=157.36 KB srcs=2.18 KB params=1.05 KB 366 B   
============ =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43341                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.03558   0.0       1     
total preclassical          0.01853   0.0       1     
splitting/filtering sources 0.01335   0.0       1     
total SourceReader          0.01061   0.0       1     
store source_info           0.00251   0.0       1     
aggregate curves            1.922E-04 0.0       1     
=========================== ========= ========= ======