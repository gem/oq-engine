Classical PSHA that utilises Christchurch-specific gsims and GMtoLHC horizontal component conversion
====================================================================================================

============== ===================
checksum32     2_056_038_439      
date           2020-03-13T11:22:03
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 4, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     20                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
amplification           `amplification.csv <amplification.csv>`_                    
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.xml <site_model.xml>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
smb1      1.00000 2               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================== =========== ========================================= ============================
grp_id gsims                                                  distances   siteparams                                ruptparams                  
====== ====================================================== =========== ========================================= ============================
0      '[Bradley2013bChchMaps]' '[McVerry2006ChchStressDrop]' rjb rrup rx lat lon siteclass vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ====================================================== =========== ========================================= ============================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      X    1            0.00171   2.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
X    0.00171  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00235 NaN    0.00235 0.00235 1      
read_source_model  0.01751 NaN    0.01751 0.01751 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ===================================== ========
task              sent                                  received
read_source_model                                       3.3 KB  
preclassical      srcs=3.09 KB params=646 B gsims=292 B 369 B   
================= ===================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66975                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.02762   0.0       1     
total read_source_model     0.01751   0.0       1     
store source_info           0.00243   0.0       1     
total preclassical          0.00235   1.10938   1     
aggregate curves            3.924E-04 0.0       1     
splitting/filtering sources 1.807E-04 0.0       1     
=========================== ========= ========= ======