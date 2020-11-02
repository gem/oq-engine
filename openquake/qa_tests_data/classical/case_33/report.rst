Etna No Topo
============

============== ====================
checksum32     2_796_600_629       
date           2020-11-02T09:15:03 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 1, num_levels = 28, num_rlzs = 1

Parameters
----------
=============================== ========================================
calculation_mode                'preclassical'                          
number_of_logic_tree_samples    0                                       
maximum_distance                {'default': [(1.0, 50.0), (10.0, 50.0)]}
investigation_time              50.0                                    
ses_per_logic_tree_path         1                                       
truncation_level                3.0                                     
rupture_mesh_spacing            1.0                                     
complex_fault_mesh_spacing      1.0                                     
width_of_mfd_bin                0.1                                     
area_source_discretization      1.0                                     
pointsource_distance            None                                    
ground_motion_correlation_model None                                    
minimum_intensity               {}                                      
random_seed                     23                                      
master_seed                     0                                       
ses_seed                        42                                      
=============================== ========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ======================= ====
grp_id gsim                    rlzs
====== ======================= ====
0      '[TusaLanger2016Rhypo]' [0] 
====== ======================= ====

Required parameters per tectonic region type
--------------------------------------------
===== ======================= ========= ========== ==========
et_id gsims                   distances siteparams ruptparams
===== ======================= ========= ========== ==========
0     '[TusaLanger2016Rhypo]' rhypo     vs30       mag       
===== ======================= ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
SVF       S    0.00234   1         150         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.00234  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       1      0.00277 nan    0.00277 0.00277
read_source_model  1      0.00247 nan    0.00247 0.00247
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.66 KB 
preclassical           241 B   
================= ==== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47020, maxmem=0.3 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.06271  0.0       1     
composite source model    0.05800  0.0       1     
total preclassical        0.00277  0.0       1     
total read_source_model   0.00247  0.0       1     
========================= ======== ========= ======