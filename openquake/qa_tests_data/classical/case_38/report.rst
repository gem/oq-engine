Subduction backbone logic tree - 9 branch
=========================================

============== ===================
checksum32     347,202,642        
date           2019-06-21T09:42:31
engine_version 3.6.0-git17fd0581aa
============== ===================

num_sites = 2, num_levels = 8, num_rlzs = 9

Parameters
----------
=============================== ===================
calculation_mode                'preclassical'     
number_of_logic_tree_samples    0                  
maximum_distance                {'default': 1000.0}
investigation_time              1.0                
ses_per_logic_tree_path         1                  
truncation_level                20.0               
rupture_mesh_spacing            1.0                
complex_fault_mesh_spacing      10.0               
width_of_mfd_bin                0.05               
area_source_discretization      1.0                
ground_motion_correlation_model None               
minimum_intensity               {}                 
random_seed                     23                 
master_seed                     0                  
ses_seed                        42                 
=============================== ===================

Input files
-----------
======================= ================================================================================
Name                    File                                                                            
======================= ================================================================================
gsim_logic_tree         `gmpe_logic_tree_interface_9branch.xml <gmpe_logic_tree_interface_9branch.xml>`_
job_ini                 `job.ini <job.ini>`_                                                            
source_model_logic_tree `peer_source_model_logic_tree.xml <peer_source_model_logic_tree.xml>`_          
======================= ================================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
PEERIF    1.00000 simple(9)       9               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================= ========= ============ ==========
grp_id gsims                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             distances siteparams   ruptparams
====== ================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================= ========= ============ ==========
0      '[BCHydroSERASInter]' '[BCHydroSERASInter]\nsigma_mu_epsilon = -1.732051' '[BCHydroSERASInter]\nsigma_mu_epsilon = 1.732051' '[BCHydroSERASInter]\ntheta6_adjustment = -0.0015' '[BCHydroSERASInter]\ntheta6_adjustment = -0.0015\nsigma_mu_epsilon = -1.732051' '[BCHydroSERASInter]\ntheta6_adjustment = -0.0015\nsigma_mu_epsilon = 1.732051' '[BCHydroSERASInter]\ntheta6_adjustment = 0.0015' '[BCHydroSERASInter]\ntheta6_adjustment = 0.0015\nsigma_mu_epsilon = -1.732051' '[BCHydroSERASInter]\ntheta6_adjustment = 0.0015\nsigma_mu_epsilon = 1.732051' rrup      backarc vs30 mag       
====== ================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================================= ========= ============ ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=9)
  0,'[BCHydroSERASInter]': [0]
  0,'[BCHydroSERASInter]\nsigma_mu_epsilon = -1.732051': [5]
  0,'[BCHydroSERASInter]\nsigma_mu_epsilon = 1.732051': [4]
  0,'[BCHydroSERASInter]\ntheta6_adjustment = -0.0015': [1]
  0,'[BCHydroSERASInter]\ntheta6_adjustment = -0.0015\nsigma_mu_epsilon = -1.732051': [3]
  0,'[BCHydroSERASInter]\ntheta6_adjustment = -0.0015\nsigma_mu_epsilon = 1.732051': [2]
  0,'[BCHydroSERASInter]\ntheta6_adjustment = 0.0015': [6]
  0,'[BCHydroSERASInter]\ntheta6_adjustment = 0.0015\nsigma_mu_epsilon = -1.732051': [8]
  0,'[BCHydroSERASInter]\ntheta6_adjustment = 0.0015\nsigma_mu_epsilon = 1.732051': [7]>

Number of ruptures per tectonic region type
-------------------------------------------
================================ ====== ==================== ============ ============
source_model                     grp_id trt                  eff_ruptures tot_ruptures
================================ ====== ==================== ============ ============
PEERInterface_Characteristic.xml 0      Subduction Interface 1            1           
================================ ====== ==================== ============ ============

Slowest sources
---------------
====== ============ ==== ===== ===== ============ ========= ========= =======
grp_id source_id    code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ============ ==== ===== ===== ============ ========= ========= =======
0      PEERS3C3_TOR X    0     154   1            0.00257   2.00000   1.13863
====== ============ ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.00257   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00309 NaN    0.00309 0.00309 1      
read_source_models 0.03496 NaN    0.03496 0.03496 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ======================================================= ========
task               sent                                                    received
preclassical       srcs=5.25 KB gsims=1.09 KB params=518 B srcfilter=220 B 343 B   
read_source_models converter=313 B fnames=123 B                            5.71 KB 
================== ======================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.03496   0.0       1     
managing sources         0.00332   0.0       1     
total preclassical       0.00309   0.0       1     
store source_info        0.00168   0.0       1     
aggregate curves         1.442E-04 0.0       1     
======================== ========= ========= ======