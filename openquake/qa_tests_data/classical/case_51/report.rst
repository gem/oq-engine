Classical PSHA — Area Source
============================

============== ====================
checksum32     2_226_276_800       
date           2020-07-31T16:43:51 
engine_version 3.10.0-git684982d357
============== ====================

num_sites = 4, num_levels = 30, num_rlzs = 1

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1, 200.0), (10, 200.0)]}
investigation_time              50.0                                  
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            2.0                                   
complex_fault_mesh_spacing      2.0                                   
width_of_mfd_bin                0.2                                   
area_source_discretization      10.0                                  
pointsource_distance            {'default': [(1, 100.0), (10, 100.0)]}
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     23                                    
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================================================================== ========= ========== ==========
grp_id gsims                                                                                 distances siteparams ruptparams
====== ===================================================================================== ========= ========== ==========
0      '[ModifiableGMPE]\ngmpe.AkkarEtAlRjb2014 = {}\nset_between_epsilon.epsilon_tau = 0.5' rjb       vs30       mag rake  
====== ===================================================================================== ========= ========== ==========

Slowest sources
---------------
========= ==== ============ ========= ========= ============
source_id code multiplicity calc_time num_sites eff_ruptures
========= ==== ============ ========= ========= ============
1         A    1            0.00674   0.39183   416         
========= ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00674  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.02096 NaN    0.02096 0.02096 1      
read_source_model  0.00249 NaN    0.00249 0.00249 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ======================================= ========
task              sent                                    received
read_source_model                                         1.72 KB 
preclassical      srcs=1.99 KB params=1.17 KB gsims=938 B 2.56 KB 
classical                                                 0 B     
================= ======================================= ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_44272                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.07343  0.77344   1     
total preclassical          0.02096  1.73828   1     
splitting/filtering sources 0.01290  0.01953   1     
total read_source_model     0.00249  0.0       1     
store source_info           0.00116  0.0       1     
aggregate curves            0.00111  0.0       1     
=========================== ======== ========= ======