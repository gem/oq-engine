Classical PSHA — Area Source
============================

============== ====================
checksum32     4_154_479_248       
date           2020-11-02T09:37:05 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 4, num_levels = 30, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.2                                       
area_source_discretization      10.0                                      
pointsource_distance            {'default': [(1.0, 100.0), (10.0, 100.0)]}
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     23                                        
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
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ===================================================================================== ====
grp_id gsim                                                                                  rlzs
====== ===================================================================================== ====
0      '[ModifiableGMPE]\ngmpe.AkkarEtAlRjb2014 = {}\nset_between_epsilon.epsilon_tau = 0.5' [0] 
====== ===================================================================================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ===================================================================================== ========= ========== ==========
et_id gsims                                                                                 distances siteparams ruptparams
===== ===================================================================================== ========= ========== ==========
0     '[ModifiableGMPE]\ngmpe.AkkarEtAlRjb2014 = {}\nset_between_epsilon.epsilon_tau = 0.5' rjb       vs30       mag rake  
===== ===================================================================================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         A    1.163E-04 4         416         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.163E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.326E-04 nan    5.326E-04 5.326E-04
read_source_model  1      0.00253   nan    0.00253   0.00253  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.72 KB 
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47345, maxmem=0.4 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.15724   0.0       1     
composite source model    0.14819   0.0       1     
total read_source_model   0.00253   0.0       1     
total preclassical        5.326E-04 0.0       1     
========================= ========= ========= ======