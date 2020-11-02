Event Based Hazard
==================

============== ====================
checksum32     3_998_936_114       
date           2020-11-02T08:41:55 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         100                                       
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     24                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job_hazard.ini <job_hazard.ini>`_                                        
site_model               `site_model.xml <site_model.xml>`_                                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
====== ================ ====
grp_id gsim             rlzs
====== ================ ====
0      [SadighEtAl1997] [0] 
====== ================ ====

Required parameters per tectonic region type
--------------------------------------------
===== ================== ========= ========== ==========
et_id gsims              distances siteparams ruptparams
===== ================== ========= ========== ==========
0     '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
Wood     1          1.00000 nan    1   1   1        
======== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
3         S    0.00262   1         482         
1         X    2.074E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.00262  
X    2.074E-04
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       2      0.00190 64%    6.790E-04 0.00311
read_source_model  1      0.01275 nan    0.01275   0.01275
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model                                 11.7 KB 
preclassical      srcs=13.15 KB srcfilter=2.33 KB 478 B   
================= =============================== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_46594, maxmem=1.0 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.11934   0.0       1     
composite source model    0.09787   0.0       1     
total read_source_model   0.01275   0.0       1     
total preclassical        0.00379   0.44531   2     
reading exposure          7.231E-04 0.0       1     
========================= ========= ========= ======