event based two source models
=============================

============== ===================
checksum32     1_291_658_938      
date           2020-01-16T05:30:40
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None              
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       482          0.0         
1      NaN       4            0.0         
2      NaN       482          0.0         
3      NaN       1            0.0         
====== ========= ============ ============

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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.0      
X    0.0      
==== =========

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.01511 0.01110 0.00726 0.02295 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader apply_unc=2.4 KB ltmodel=378 B fname=212 B 18.33 KB
============ ========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_43193             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.04023   0.0       1     
total SourceReader     0.03021   0.0       2     
reading exposure       6.764E-04 0.0       1     
====================== ========= ========= ======