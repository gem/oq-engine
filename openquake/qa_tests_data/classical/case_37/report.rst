Classical PSHA that utilises Christchurch-specific gsims and GMtoLHC horizontal component conversion
====================================================================================================

============== ====================
checksum32     677_658_808         
date           2020-11-02T09:36:52 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 2, num_levels = 4, num_rlzs = 2

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      None                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     20                                        
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
site_model              `site_model.xml <site_model.xml>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ============================= ====
grp_id gsim                          rlzs
====== ============================= ====
0      '[Bradley2013bChchMaps]'      [0] 
0      '[McVerry2006ChchStressDrop]' [1] 
====== ============================= ====

Required parameters per tectonic region type
--------------------------------------------
===== ====================================================== =========== ========================================= ============================
et_id gsims                                                  distances   siteparams                                ruptparams                  
===== ====================================================== =========== ========================================= ============================
0     '[Bradley2013bChchMaps]' '[McVerry2006ChchStressDrop]' rjb rrup rx lat lon siteclass vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
===== ====================================================== =========== ========================================= ============================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         X    1.462E-04 2         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
X    1.462E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.655E-04 nan    5.655E-04 5.655E-04
read_source_model  1      0.02578   nan    0.02578   0.02578  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      3.29 KB 
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47327, maxmem=0.3 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.08258   0.0       1     
composite source model    0.07509   0.0       1     
total read_source_model   0.02578   0.0       1     
total preclassical        5.655E-04 0.0       1     
========================= ========= ========= ======