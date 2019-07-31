event based two source models
=============================

============== ===================
checksum32     1,852,256,743      
date           2019-07-30T15:04:10
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 1, num_levels = 11, num_rlzs = ?

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
=========== =
#assets     1
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =====
source_id grp_id code num_ruptures calc_time num_sites weight speed
========= ====== ==== ============ ========= ========= ====== =====
========= ====== ==== ============ ========= ========= ====== =====

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
read_source_models 0.01097 0.00415 0.00803 0.01390 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=628 B fnames=204 B 13.91 KB
================== ============================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15515               time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.02194   0.0       2     
reading exposure         5.159E-04 0.0       1     
======================== ========= ========= ======