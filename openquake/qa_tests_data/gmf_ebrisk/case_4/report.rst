event based two source models
=============================

============== ===================
checksum32     1,852,256,743      
date           2019-10-01T06:08:36
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 173, num_levels = 11, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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

Exposure model
--------------
=========== ===
#assets     174
#taxonomies 4  
=========== ===

============= ======= ======= === === ========= ==========
taxonomy      mean    stddev  min max num_sites num_assets
Moderate_roof 1.02778 0.16667 1   2   36        37        
Heavy_roof    1.00000 0.0     1   1   35        35        
Weak_roof     1.00000 0.0     1   1   43        43        
Slab_roof     1.00000 0.0     1   1   59        59        
*ALL*         1.00578 0.07603 1   2   173       174       
============= ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.0       3     
X    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.01171 0.00695 0.00680 0.01663 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.35 KB ltmodel=378 B fname=198 B 17.21 KB
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23155             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.02952  0.0       1     
total SourceReader     0.02343  0.0       2     
reading exposure       0.00407  0.0       1     
====================== ======== ========= ======