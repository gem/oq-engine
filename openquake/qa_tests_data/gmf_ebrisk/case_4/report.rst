event based two source models
=============================

============== ====================
checksum32     1_318_489_618       
date           2020-11-02T09:35:28 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 30, num_rlzs = 2

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         2                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model 'JB2009'                                  
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
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                              
job_ini                  `job_haz.ini <job_haz.ini>`_                                              
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
====== ===================== ======
grp_id gsim                  rlzs  
====== ===================== ======
0      '[BooreAtkinson2008]' [0, 1]
1      '[AkkarBommer2010]'   [0]   
2      '[AkkarBommer2010]'   [1]   
====== ===================== ======

Required parameters per tectonic region type
--------------------------------------------
===== ===================== ========= ========== ==========
et_id gsims                 distances siteparams ruptparams
===== ===================== ========= ========== ==========
0     '[BooreAtkinson2008]' rjb       vs30       mag rake  
1     '[BooreAtkinson2008]' rjb       vs30       mag rake  
2     '[AkkarBommer2010]'   rjb       vs30       mag rake  
3     '[AkkarBommer2010]'   rjb       vs30       mag rake  
===== ===================== ========= ========== ==========

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
tax1     1          1.00000 nan    1   1   1        
======== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         S    0.00275   1         482         
2;0       S    0.00253   1         4           
2;1       X    1.736E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.00528  
X    1.736E-04
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       3      0.00237 45%    8.395E-04 0.00325
read_source_model  2      0.00586 68%    0.00184   0.00989
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model converter=664 B fname=198 B     13.67 KB
preclassical      srcs=14.42 KB srcfilter=3.85 KB 721 B   
================= =============================== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47207, maxmem=1.1 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          1.05145   0.0       1     
composite source model    1.02846   0.0       1     
total read_source_model   0.01173   0.35938   2     
total preclassical        0.00710   0.57031   3     
reading exposure          6.359E-04 0.0       1     
========================= ========= ========= ======