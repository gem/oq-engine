Classical PSHA that utilises Christchurch-specific gsims and GMtoLHC horizontal component conversion
====================================================================================================

============== ===================
checksum32     3,681,125,057      
date           2019-10-01T07:01:08
engine_version 3.8.0-gitbd71c2f960
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
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.xml <site_model.xml>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
smb1      1.00000 simple(2)       2               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================== =========== ========================================= ============================
grp_id gsims                                                  distances   siteparams                                ruptparams                  
====== ====================================================== =========== ========================================= ============================
0      '[Bradley2013bChchMaps]' '[McVerry2006ChchStressDrop]' rjb rrup rx lat lon siteclass vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ====================================================== =========== ========================================= ============================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
1         0      X    1            0.00167   2.00000   1.00000      600  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.00167   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.01761 NaN    0.01761 0.01761 1      
preclassical       0.00206 NaN    0.00206 0.00206 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ===================================== ========
task         sent                                  received
SourceReader                                       4.43 KB 
preclassical srcs=2.93 KB params=525 B gsims=292 B 342 B   
============ ===================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6623              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.02664   0.0       1     
total SourceReader     0.01761   0.0       1     
store source_info      0.00246   0.0       1     
total preclassical     0.00206   0.0       1     
aggregate curves       2.546E-04 0.0       1     
====================== ========= ========= ======