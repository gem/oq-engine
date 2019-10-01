Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     3,629,822,399      
date           2019-10-01T07:00:54
engine_version 3.8.0-gitbd71c2f960
============== ===================

num_sites = 1, num_levels = 8, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================== ========= ========== ==========
grp_id gsims                                  distances siteparams ruptparams
====== ====================================== ========= ========== ==========
0      '[AkkarBommer2010]' '[SadighEtAl1997]' rjb rrup  vs30       mag rake  
====== ====================================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   482          482         
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
1         0      S    482          0.00564   1.00000   482          85,417
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.00564   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00445 NaN    0.00445 0.00445 1      
preclassical       0.00618 NaN    0.00618 0.00618 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ===================================== ========
task         sent                                  received
SourceReader                                       2.62 KB 
preclassical srcs=1.12 KB params=557 B gsims=258 B 342 B   
============ ===================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6569              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.01347   0.0       1     
total preclassical     0.00618   0.0       1     
total SourceReader     0.00445   0.0       1     
store source_info      0.00284   0.0       1     
reading exposure       4.783E-04 0.0       1     
aggregate curves       2.627E-04 0.0       1     
====================== ========= ========= ======