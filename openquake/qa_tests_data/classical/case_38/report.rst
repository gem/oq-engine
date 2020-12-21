Subduction backbone logic tree - 9 branch
=========================================

============== ====================
checksum32     2_313_082_878       
date           2020-11-02T09:36:49 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 2, num_levels = 8, num_rlzs = 9

Parameters
----------
=============================== ============================================
calculation_mode                'preclassical'                              
number_of_logic_tree_samples    0                                           
maximum_distance                {'default': [(1.0, 1000.0), (10.0, 1000.0)]}
investigation_time              1.0                                         
ses_per_logic_tree_path         1                                           
truncation_level                20.0                                        
rupture_mesh_spacing            1.0                                         
complex_fault_mesh_spacing      10.0                                        
width_of_mfd_bin                0.05                                        
area_source_discretization      1.0                                         
pointsource_distance            None                                        
ground_motion_correlation_model None                                        
minimum_intensity               {}                                          
random_seed                     23                                          
master_seed                     0                                           
ses_seed                        42                                          
=============================== ============================================

Input files
-----------
======================= ================================================================================
Name                    File                                                                            
======================= ================================================================================
gsim_logic_tree         `gmpe_logic_tree_interface_9branch.xml <gmpe_logic_tree_interface_9branch.xml>`_
job_ini                 `job.ini <job.ini>`_                                                            
site_model              `site_model.xml <site_model.xml>`_                                              
source_model_logic_tree `peer_source_model_logic_tree.xml <peer_source_model_logic_tree.xml>`_          
======================= ================================================================================

Composite source model
----------------------
====== ================================================================================== ====
grp_id gsim                                                                               rlzs
====== ================================================================================== ====
0      '[BCHydroESHM20SInter]'                                                            [0] 
0      '[BCHydroESHM20SInter]\nsigma_mu_epsilon = -1.732051'                              [5] 
0      '[BCHydroESHM20SInter]\nsigma_mu_epsilon = 1.732051'                               [4] 
0      '[BCHydroESHM20SInter]\ntheta6_adjustment = -0.0015'                               [1] 
0      '[BCHydroESHM20SInter]\ntheta6_adjustment = -0.0015\nsigma_mu_epsilon = -1.732051' [3] 
0      '[BCHydroESHM20SInter]\ntheta6_adjustment = -0.0015\nsigma_mu_epsilon = 1.732051'  [2] 
0      '[BCHydroESHM20SInter]\ntheta6_adjustment = 0.0015'                                [6] 
0      '[BCHydroESHM20SInter]\ntheta6_adjustment = 0.0015\nsigma_mu_epsilon = -1.732051'  [8] 
0      '[BCHydroESHM20SInter]\ntheta6_adjustment = 0.0015\nsigma_mu_epsilon = 1.732051'   [7] 
====== ================================================================================== ====

Required parameters per tectonic region type
--------------------------------------------
===== =================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================== ========= ========== ==========
et_id gsims                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               distances siteparams ruptparams
===== =================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================== ========= ========== ==========
0     '[BCHydroESHM20SInter]' '[BCHydroESHM20SInter]\nsigma_mu_epsilon = -1.732051' '[BCHydroESHM20SInter]\nsigma_mu_epsilon = 1.732051' '[BCHydroESHM20SInter]\ntheta6_adjustment = -0.0015' '[BCHydroESHM20SInter]\ntheta6_adjustment = -0.0015\nsigma_mu_epsilon = -1.732051' '[BCHydroESHM20SInter]\ntheta6_adjustment = -0.0015\nsigma_mu_epsilon = 1.732051' '[BCHydroESHM20SInter]\ntheta6_adjustment = 0.0015' '[BCHydroESHM20SInter]\ntheta6_adjustment = 0.0015\nsigma_mu_epsilon = -1.732051' '[BCHydroESHM20SInter]\ntheta6_adjustment = 0.0015\nsigma_mu_epsilon = 1.732051' rrup      vs30 xvf   mag       
===== =================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================== ========= ========== ==========

Slowest sources
---------------
============ ==== ========= ========= ============
source_id    code calc_time num_sites eff_ruptures
============ ==== ========= ========= ============
PEERS3C3_TOR X    1.302E-04 2         1           
============ ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
X    1.302E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.422E-04 nan    5.422E-04 5.422E-04
read_source_model  1      0.10434   nan    0.10434   0.10434  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      5.64 KB 
preclassical           250 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47323, maxmem=0.4 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.20420   0.0       1     
composite source model    0.19648   0.0       1     
total read_source_model   0.10434   0.0       1     
total preclassical        5.422E-04 0.0       1     
========================= ========= ========= ======