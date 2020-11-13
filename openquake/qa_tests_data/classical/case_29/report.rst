NNParametric
============

============== ====================
checksum32     4_204_390_297       
date           2020-11-02T09:36:52 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 500), (10.0, 500)]}
investigation_time              1.0                                   
ses_per_logic_tree_path         1                                     
truncation_level                2.0                                   
rupture_mesh_spacing            2.0                                   
complex_fault_mesh_spacing      2.0                                   
width_of_mfd_bin                0.1                                   
area_source_discretization      5.0                                   
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     23                                    
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Composite source model
----------------------
====== ===================== ====
grp_id gsim                  rlzs
====== ===================== ====
0      '[BooreAtkinson2008]' [0] 
====== ===================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ===================== ========= ========== ==========
et_id gsims                 distances siteparams ruptparams
===== ===================== ========= ========== ==========
0     '[BooreAtkinson2008]' rjb       vs30       mag rake  
===== ===================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
test      N    2.532E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    2.532E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      7.150E-04 nan    7.150E-04 7.150E-04
read_source_model  1      0.00212   nan    0.00212   0.00212  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      2.2 KB  
preclassical           242 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47326, maxmem=0.3 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.09843   0.0       1     
composite source model    0.09366   0.0       1     
total read_source_model   0.00212   0.0       1     
total preclassical        7.150E-04 0.0       1     
========================= ========= ========= ======