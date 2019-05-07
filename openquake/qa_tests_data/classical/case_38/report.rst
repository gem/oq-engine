Subduction backbone logic tree - 9 branch
=========================================

============== ===================
checksum32     2,927,813,965      
date           2019-05-06T16:51:05
engine_version 3.5.0-gitb5a44a2026
============== ===================

num_sites = 2, num_levels = 8, num_rlzs = 9

Parameters
----------
=============================== ===================
calculation_mode                'classical'        
number_of_logic_tree_samples    0                  
maximum_distance                {'default': 1000.0}
investigation_time              1.0                
ses_per_logic_tree_path         1                  
truncation_level                20.0               
rupture_mesh_spacing            1.0                
complex_fault_mesh_spacing      1.0                
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
job_ini                 `job_peer.ini <job_peer.ini>`_                                                  
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
====== ============ ==== ===== ====== ============ ========= ========= =======
grp_id source_id    code gidx1 gidx2  num_ruptures calc_time num_sites weight 
====== ============ ==== ===== ====== ============ ========= ========= =======
0      PEERS3C3_TOR X    0     13,231 1            0.00608   2.00000   1.41421
====== ============ ==== ===== ====== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.00608   1     
==== ========= ======

Information about the tasks
---------------------------
====================== ======= ========= ======= ======= =======
operation-duration     mean    stddev    min     max     outputs
read_source_models     13      NaN       13      13      1      
classical_split_filter 0.01749 NaN       0.01749 0.01749 1      
build_hazard_stats     0.01044 2.697E-05 0.01042 0.01046 2      
====================== ======= ========= ======= ======= =======

Data transfer
-------------
====================== =========================================================== =========
task                   sent                                                        received 
read_source_models     converter=313 B fnames=130 B                                312.22 KB
classical_split_filter srcs=311.75 KB gsims=1.09 KB params=518 B srcfilter=219 B   2.36 KB  
build_hazard_stats     pgetter=17.97 KB hstats=476 B N=28 B individual_curves=26 B 1.81 KB  
====================== =========================================================== =========

Slowest operations
------------------
============================ ======== ========= ======
operation                    time_sec memory_mb counts
============================ ======== ========= ======
ClassicalCalculator.run      17       7.20703   1     
total read_source_models     13       8.00781   1     
export                       0.05276  0.09375   1     
store source model           0.03696  1.18359   1     
total build_hazard_stats     0.02088  2.63281   2     
total classical_split_filter 0.01749  2.61328   1     
managing sources             0.01498  0.83203   1     
combine pmaps                0.01323  2.53516   2     
filtering/splitting sources  0.01097  1.91016   1     
compute stats                0.00709  0.09375   2     
store source_info            0.00351  0.01562   1     
saving probability maps      0.00302  0.01953   1     
aggregate curves             0.00286  0.05469   1     
get_poes                     0.00266  0.0       1     
saving statistics            0.00254  0.00391   2     
make_contexts                0.00151  0.0       1     
============================ ======== ========= ======