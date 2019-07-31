Event Based Bogota
==================

============== ===================
checksum32     4,020,014,859      
date           2019-07-30T15:03:53
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 5, num_levels = 104, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    100               
maximum_distance                {'default': 100.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ==================================================================
Name                     File                                                              
======================== ==================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                        
gsim_logic_tree          `logic_tree_gmpe_simplified.xml <logic_tree_gmpe_simplified.xml>`_
job_ini                  `job.ini <job.ini>`_                                              
site_model               `site_model_bog.xml <site_model_bog.xml>`_                        
source_model_logic_tree  `logic_tree_source_model.xml <logic_tree_source_model.xml>`_      
structural_vulnerability `vulnerability_model_bog.xml <vulnerability_model_bog.xml>`_      
======================== ==================================================================

Exposure model
--------------
=========== =
#assets     5
#taxonomies 4
=========== =

===================== ======= ====== === === ========= ==========
taxonomy              mean    stddev min max num_sites num_assets
MCF/LWAL+DUC/HBET:3,6 1.00000 0.0    1   1   2         2         
MUR/HBET:4,5          1.00000 NaN    1   1   1         1         
CR/LDUAL+DUC          1.00000 NaN    1   1   1         1         
CR/LFINF+DUC          1.00000 NaN    1   1   1         1         
*ALL*                 1.00000 0.0    1   1   5         5         
===================== ======= ====== === === ========= ==========

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
C    0.0       1     
P    0.0       122   
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.25401 0.28124 0.05514 0.45287 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=628 B fnames=227 B 70.82 KB
================== ============================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15486               time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.50801   0.37891   2     
reading exposure         4.790E-04 0.0       1     
======================== ========= ========= ======